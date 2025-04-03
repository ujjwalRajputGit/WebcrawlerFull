import re
import time
import random
from enum import Enum
from celery_worker import celery_app
from utils.fetcher import fetch_page, fetch_page_async
from parsers import get_parser
from constants import ParserType
from db.storage import Storage
from utils.logger import get_logger
from urllib.parse import urlparse, urljoin, urlsplit, urlunsplit
from typing import Set, Dict, List
from bs4 import BeautifulSoup
from utils.config import PAGINATION_PATTERNS, PARSERS_TO_USE
import asyncio
import aiohttp

logger = get_logger(__name__)

# Initialize storage
storage = Storage()

def normalize_url(url):
    """Normalize URL to avoid duplicates."""
    try:
        # Parse the URL
        parsed = urlsplit(url)
        
        # Remove common session/tracking parameters
        query_params = parsed.query.split('&')
        filtered_params = []
        excluded_params = ['utm_source', 'utm_medium', 'utm_campaign', 'ref', 'session', 
                          'tracking', 'click', 'affiliate', 'source']
        
        for param in query_params:
            if param and '=' in param:
                param_name = param.split('=')[0].lower()
                if not any(excluded in param_name for excluded in excluded_params):
                    filtered_params.append(param)
        
        new_query = '&'.join(filtered_params)
        
        # Reconstruct it with a consistent format
        return urlunsplit((
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path.rstrip('/'),
            new_query,
            ''  # No fragment
        ))
    except Exception as e:
        logger.warning(f"Error normalizing URL {url}: {e}")
        return url

def find_urls(html: str, base_url: str, domain_netloc: str):
    """
    Unified URL discovery function with better performance.
    
    Args:
        html (str): HTML content to parse
        base_url (str): Base URL of the website
        domain_netloc (str): Domain netloc for filtering internal links
    
    Returns:
        list: Combined list of URLs to crawl
    """
    next_urls = set()
    pagination_urls = set()
    
    try:
        soup = BeautifulSoup(html, "html.parser")
        
        # Find all links
        for a_tag in soup.find_all("a", href=True):
            href = a_tag.get('href')
            if not href:
                continue
                
            full_url = urljoin(base_url, href)
            parsed_url = urlparse(full_url)
            
            # Keep only internal links
            if not parsed_url.netloc or parsed_url.netloc == domain_netloc:
                # Check if it's a pagination link
                is_pagination = False
                
                # Check text for pagination indicators
                text = a_tag.get_text().strip().lower()
                pagination_indicators = ['next', 'page', '»', '>', 'load more', 'show more']
                if any(indicator in text for indicator in pagination_indicators):
                    is_pagination = True
                
                # Check URL patterns for pagination
                if not is_pagination:
                    for pattern in PAGINATION_PATTERNS:
                        if re.search(pattern, href):
                            is_pagination = True
                            break
                
                if is_pagination:
                    pagination_urls.add(full_url)
                else:
                    next_urls.add(full_url)
        
        # Return pagination URLs first (they get priority)
        return list(pagination_urls) + list(next_urls - pagination_urls)
        
    except Exception as e:
        logger.error(f"Error finding URLs: {e}")
        return []

def generate_sequential_urls(product_urls, max_urls=30):
    """Generate sequential URLs based on patterns in discovered URLs."""
    if len(product_urls) < 3:
        return []
    
    sequential_urls = set()
    
    # Look for numeric patterns in URLs
    number_patterns = [
        r'/(\d+)(?:/|$)',     # /123/
        r'p=(\d+)',           # p=123
        r'page=(\d+)',        # page=123
        r'-p(\d+)',           # -p123
        r'_(\d+)\.html'       # _123.html
    ]
    
    # Convert set to list for easier manipulation
    product_urls_list = list(product_urls)
    
    # Sample some URLs to analyze patterns (don't check all to save time)
    sample_size = min(10, len(product_urls_list))
    sample_urls = random.sample(product_urls_list, sample_size)
    
    for pattern in number_patterns:
        # Check if the pattern exists in our sample URLs
        pattern_found = False
        for url in sample_urls:
            match = re.search(pattern, url)
            if match:
                pattern_found = True
                num = int(match.group(1))
                
                # Generate URLs with nearby numbers
                for i in range(1, 4):  # Generate fewer nearby numbers to reduce load
                    # Try incrementing
                    new_num = num + i
                    new_url = re.sub(pattern, lambda m: m.group(0).replace(m.group(1), str(new_num)), url)
                    sequential_urls.add(new_url)
                    
                    # Try decrementing if number is large enough
                    if num > i:
                        new_num = num - i
                        new_url = re.sub(pattern, lambda m: m.group(0).replace(m.group(1), str(new_num)), url)
                        sequential_urls.add(new_url)
        
        # If we found this pattern, don't check others to avoid excessive URLs
        if pattern_found:
            break
    
    # Filter out URLs that are already in product_urls and limit the number
    new_urls = [url for url in sequential_urls if url not in product_urls]
    return new_urls[:max_urls]

@celery_app.task(name="tasks.crawl", bind=True, 
                 autoretry_for=(Exception,), 
                 retry_kwargs={'max_retries': 1, 'countdown': 10},
                 rate_limit='10/m')
def crawl_task(self, domains: List[str], max_depth:int) -> Dict:
    """
    Implementation of the crawl task with detailed status updates.
    """
    if not domains:
        logger.warning("No domains provided for crawling")
        return {"status": "error", "message": "No domains provided for crawling"}
    
    if not max_depth:
        logger.info("No max depth provided for crawling")
        return {"status": "error", "message": "No max depth provided for crawling"}

    try:
        start_time = time.time()
        task_id = self.request.id
        
        # Update task state to show it's starting
        self.update_state(state='PROGRESS', meta={
            'status': 'starting',
            'task_id': task_id,
            'domains': domains,
            'max_depth': max_depth
        })
        
        # Process domains sequentially within this task
        all_results = []
        domain_statuses = {domain: {'status': 'pending', 'depth': 0, 'depth_progress': '0/0', 'urls_discovered': 0} for domain in domains}
        
        for i, domain in enumerate(domains):
            # Update status to show we're starting this domain
            domain_statuses[domain]['status'] = 'crawling'
            self.update_state(state='PROGRESS', meta={
                'status': 'processing',
                'task_id': task_id,
                'progress': f"{i}/{len(domains)}",
                'domains_completed': i,
                'domains_total': len(domains),
                'current_domain': domain,
                'domain_statuses': domain_statuses
            })
            
            # Process the domain with a status update callback
            result = process_domain(domain, max_depth, task_id, 
                                    lambda status_update: update_domain_status(self, domain, status_update, domain_statuses, i, len(domains)))
            
            all_results.append(result)
            
            # Mark domain as completed in status
            domain_statuses[domain]['status'] = 'completed'
            domain_statuses[domain]['urls_discovered'] = result.get('urls_count', 0)
            
            # Update progress after each domain
            self.update_state(state='PROGRESS', meta={
                'status': 'processing',
                'task_id': task_id,
                'progress': f"{i+1}/{len(domains)}",
                'domains_completed': i+1,
                'domains_total': len(domains),
                'domain_statuses': domain_statuses
            })
        
        # Aggregate results directly
        return aggregate_results_locally(all_results, task_id, domains, start_time)
    except Exception as e:
        logger.error(f"Task {self.request.id} failed: {str(e)}")
        raise

def update_domain_status(task, domain, status_update, domain_statuses, domains_completed, total_domains):
    """
    Update the domain status and propagate to the main task status.
    """
    # Update this domain's status in our tracking dict
    domain_statuses[domain].update(status_update)
    
    # Update the main task status
    task.update_state(state='PROGRESS', meta={
        'status': 'processing',
        'progress': f"{domains_completed}/{total_domains}",
        'domains_completed': domains_completed,
        'domains_total': total_domains,
        'current_domain': domain,
        'domain_statuses': domain_statuses
    })

def process_domain(domain: str, max_depth: int, parent_task_id: str, status_callback=None) -> Dict:
    """
    Process a single domain within the main task using async for improved performance.
    """
    logger.info(f"🕵️‍♂️ Starting deep crawl for domain: {domain}")
    
    # Run the async function using asyncio
    try:
        # Create a status reporting task that uses the callback
        class StatusReportingTask:
            def update_state(self, state, meta):
                logger.info(f"Domain {domain} progress: {meta}")
                if status_callback:
                    status_callback(meta)
        
        task = StatusReportingTask()
        
        # Run the async function
        return asyncio.run(crawl_single_domain_async(task, domain, max_depth, parent_task_id))
    except Exception as e:
        logger.error(f"Error crawling domain {domain}: {str(e)}")
        return {
            "status": "error",
            "domain": domain,
            "error": str(e)
        }

def aggregate_results_locally(domain_results, task_id, domains, start_time):
    """
    Local version of aggregate_results that doesn't need to be a Celery task.
    """
    try:
        # Same aggregation logic as the Celery task
        parser_stats = {
            "simple": {"total": 0, "domains": set(), "unique": 0},
            "config": {"total": 0, "domains": set(), "unique": 0},
            "ai": {"total": 0, "domains": set(), "unique": 0},
            "sequential": {"total": 0, "domains": set(), "unique": 0}
        }
        urls_count_by_domain = {}
        total_urls_by_parser = {}
        
        for result in domain_results:
            if result["status"] == "completed":
                domain = result["domain"]
                urls_count_by_domain[domain] = result["urls_count"]
                
                # Aggregate parser statistics
                for parser_type in ["simple", "config", "ai", "sequential"]:
                    parser_stats[parser_type]["total"] += result["parser_stats"][parser_type]["total"]
                    parser_stats[parser_type]["unique"] += result["parser_stats"][parser_type]["unique"]
                    parser_stats[parser_type]["domains"].update(result["parser_stats"][parser_type]["domains"])
                
                # Aggregate URL counts by parser
                for parser_type, count in result.get("parser_url_counts", {}).items():
                    total_urls_by_parser[parser_type] = total_urls_by_parser.get(parser_type, 0) + count
        
        end_time = time.time()
        duration = end_time - start_time

        logger.info(f"✅ Deep crawl completed in {duration:.2f} seconds")
        
        # Convert sets to lists for JSON serialization
        for parser_type in parser_stats:
            parser_stats[parser_type]["domains"] = list(parser_stats[parser_type]["domains"])
        
        return {
            "status": "completed",
            "task_id": task_id,
            "duration": f"{duration:.2f} seconds",
            "domains": domains,
            "urls_count": urls_count_by_domain,
            "total_urls": sum(urls_count_by_domain.values()),
            "parser_stats": {
                "simple": {
                    "total": parser_stats['simple']['total'],
                    "unique": parser_stats['simple']['unique'],
                    "domains": len(parser_stats['simple']['domains'])
                },
                "config": {
                    "total": parser_stats['config']['total'],
                    "unique": parser_stats['config']['unique'],
                    "domains": len(parser_stats['config']['domains'])
                },
                "ai": {
                    "total": parser_stats['ai']['total'],
                    "unique": parser_stats['ai']['unique'],
                    "domains": len(parser_stats['ai']['domains'])
                },
                "sequential": {
                    "total": parser_stats['sequential']['total'],
                    "unique": parser_stats['sequential']['unique'],
                    "domains": len(parser_stats['sequential']['domains'])
                }
            },
            "urls_by_parser": total_urls_by_parser
        }
    except Exception as e:
        logger.error(f"Error aggregating results: {str(e)}")
        raise

@celery_app.task(name="tasks.crawl_single_domain", bind=True,
                autoretry_for=(Exception,),
                retry_kwargs={'max_retries': 1, 'countdown': 10},
                rate_limit='10/m')
def crawl_single_domain(self, domain: str, max_depth: int, parent_task_id: str) -> Dict:
    """
    Process a single domain for crawling using async for improved performance.
    """
    logger.info(f"🕵️‍♂️ Starting deep crawl for domain: {domain}")
    
    # Run the async function using asyncio
    return asyncio.run(crawl_single_domain_async(self, domain, max_depth, parent_task_id))

async def crawl_single_domain_async(task, domain: str, max_depth: int, parent_task_id: str) -> Dict:
    """
    Asynchronous implementation of domain crawling with detailed status updates.
    """
    try:
        # Initialize parsers for this subtask
        parsers = {
            ParserType.SIMPLE: get_parser(ParserType.SIMPLE),
            ParserType.CONFIG: get_parser(ParserType.CONFIG),
            ParserType.AI: get_parser(ParserType.AI)
        }
        
        # Statistics tracking for this domain
        parser_stats = {
            "simple": {"total": 0, "domains": set(), "unique": 0},
            "config": {"total": 0, "domains": set(), "unique": 0},
            "ai": {"total": 0, "domains": set(), "unique": 0},
            "sequential": {"total": 0, "domains": set(), "unique": 0}
        }
        
        # Track which parser found each URL first
        url_first_found_by = {}
        
        # Track visited URLs to avoid duplicates
        visited_urls = set()
        urls_to_visit = [domain]
        
        # Store all discovered product URLs for this domain
        domain_product_urls = set()
        
        # Extract domain for checking internal links
        domain_netloc = urlparse(domain).netloc
        
        # Control crawl depth
        current_depth = 0
        
        # Create an aiohttp session for reuse
        async with aiohttp.ClientSession() as session:
            # Process URLs at each depth level
            while current_depth < max_depth and urls_to_visit:
                logger.info(f"Crawling depth {current_depth}: Processing {len(urls_to_visit)} URLs")
                
                # Update status at the start of each depth
                task.update_state(state='PROGRESS', meta={
                    'status': 'crawling',
                    'domain': domain,
                    'depth': current_depth,
                    'depth_progress': f"0/{len(urls_to_visit)}",
                    'urls_discovered': len(domain_product_urls),
                    'total_urls_to_process': len(urls_to_visit)
                })
                
                next_depth_urls = []
                processed_count = 0
                total_count = len(urls_to_visit)
                
                # Process URLs in batches to avoid overwhelming servers
                batch_size = 10  # Adjust based on target site capabilities
                for i in range(0, len(urls_to_visit), batch_size):
                    batch = urls_to_visit[i:i+batch_size]
                    batch = [url for url in batch if url not in visited_urls]
                    
                    # Mark as visited before processing
                    for url in batch:
                        visited_urls.add(url)
                    
                    # Create tasks for concurrent fetching
                    tasks = []
                    for url in batch:
                        tasks.append(process_url(
                            url, 
                            session, 
                            parsers, 
                            PARSERS_TO_USE, 
                            domain_netloc, 
                            url_first_found_by, 
                            parser_stats, 
                            current_depth, 
                            max_depth
                        ))
                    
                    # Process batch concurrently
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results
                    for url, result in zip(batch, results):
                        processed_count += 1
                        
                        if isinstance(result, Exception):
                            logger.error(f"🔥 Error crawling {url}: {result}")
                            continue
                            
                        product_urls, next_urls = result
                        
                        if product_urls:
                            logger.info(f"Found {len(product_urls)} total product URLs on {url}")
                            domain_product_urls.update(product_urls)
                            
                            # Generate additional URLs based on patterns
                            if len(product_urls) >= 3:
                                seq_urls = generate_sequential_urls(product_urls)
                                if seq_urls:
                                    # Track statistics
                                    parser_stats["sequential"]["total"] += len(seq_urls)
                                    parser_stats["sequential"]["domains"].add(domain_netloc)
                                    
                                    # Track which URLs were found by sequential generator
                                    for found_url in seq_urls:
                                        if found_url not in url_first_found_by:
                                            url_first_found_by[found_url] = "sequential"
                                    
                                    logger.info(f"Generated {len(seq_urls)} sequential URLs")
                                    domain_product_urls.update(seq_urls)
                        
                        # Add new URLs to the next depth queue
                        for next_url in next_urls:
                            if next_url not in visited_urls and next_url not in next_depth_urls:
                                next_depth_urls.append(next_url)
                    
                    # Update progress more frequently (after each batch)
                    task.update_state(state='PROGRESS', meta={
                        'status': 'crawling',
                        'domain': domain,
                        'depth': current_depth,
                        'depth_progress': f"{processed_count}/{total_count}",
                        'urls_discovered': len(domain_product_urls),
                        'batch_progress': f"{i+batch_size if i+batch_size < total_count else total_count}/{total_count}",
                        'urls_in_next_depth': len(next_depth_urls)
                    })
                    
                    # Add a small delay between batches to be nice to the server
                    await asyncio.sleep(1)
                
                # Move to next depth
                current_depth += 1
                
                # Prioritize URLs by category patterns
                category_patterns = [
                    r'/category/', r'/collection', r'/products?/', r'/shop/', 
                    r'/department/', r'/catalog/', r'/items?/'
                ]
                
                priority_urls = []
                other_urls = []
                
                for url in next_depth_urls:
                    if any(re.search(pattern, url) for pattern in category_patterns):
                        priority_urls.append(url)
                    else:
                        other_urls.append(url)
                
                # Combine with priority order and apply limit
                urls_to_visit = (priority_urls + other_urls)[:500] if len(next_depth_urls) > 500 else next_depth_urls
                
                # Save URLs periodically
                if domain_product_urls:
                    storage.save(domain, parent_task_id, list(domain_product_urls))
                    logger.info(f"Saved {len(domain_product_urls)} URLs at depth {current_depth}")
                
                # Update status at the end of each depth
                task.update_state(state='PROGRESS', meta={
                    'status': 'crawling',
                    'domain': domain,
                    'depth': current_depth,
                    'depth_complete': True,
                    'urls_discovered': len(domain_product_urls),
                    'next_depth_urls': len(urls_to_visit)
                })
        
        # Final report for this domain
        if domain_product_urls:
            logger.info(f"✅ Total unique product URLs for {domain}: {len(domain_product_urls)}")
            
            # Final save
            storage.save(domain, parent_task_id, list(domain_product_urls))
        else:
            logger.warning(f"No product URLs found for {domain}")

        # Calculate unique URL counts by parser
        for parser_name in ["simple", "config", "ai", "sequential"]:
            unique_count = sum(1 for url, parser in url_first_found_by.items() if parser == parser_name)
            parser_stats[parser_name]["unique"] = unique_count

        # Return metadata
        return {
            "status": "completed",
            "domain": domain,
            "urls_count": len(domain_product_urls),
            "parser_stats": {
                parser_type: {
                    "total": stats["total"],
                    "domains": list(stats["domains"]),
                    "unique": stats["unique"]
                } for parser_type, stats in parser_stats.items()
            },
            # Count of URLs by parser type instead of full mapping
            "parser_url_counts": {
                parser: sum(1 for url, p in url_first_found_by.items() if p == parser)
                for parser in set(url_first_found_by.values())
            }
        }
    except Exception as e:
        logger.error(f"Error crawling domain {domain}: {str(e)}")
        return {
            "status": "error",
            "domain": domain,
            "error": str(e)
        }

async def process_url(url, session, parsers, parsers_to_use, domain_netloc, url_first_found_by, parser_stats, current_depth, max_depth):
    """
    Process a single URL asynchronously - fetch, parse, and extract links.
    """
    try:
        # Fetch page content asynchronously
        html_content = await fetch_page_async(url, session)
        if not html_content:
            # For potentially important URLs, retry with delay
            if any(keyword in url.lower() for keyword in ['product', 'category', 'collection']):
                logger.warning(f"Retrying important URL: {url}")
                await asyncio.sleep(2)  # Short delay before retry
                html_content = await fetch_page_async(url, session)
            
            if not html_content:
                logger.warning(f"Failed to fetch content for {url}")
                return set(), []
        
        # Extract product URLs with parsers
        product_urls = set()
        
        # Try each parser in the configured order
        for parser_type in parsers_to_use:
            if parser_type not in parsers:
                logger.warning(f"Unknown parser type: {parser_type}")
                continue
                
            try:
                parser = parsers[parser_type]
                urls = parser.parse(html_content, url)
                
                parser_type_str = parser_type.value if isinstance(parser_type, Enum) else str(parser_type)
                if urls:
                    # Track statistics
                    parser_stats[parser_type_str]["total"] += len(urls)
                    parser_stats[parser_type_str]["domains"].add(domain_netloc)
                    
                    # Track which URLs were found first by which parser
                    for found_url in urls:
                        if found_url not in url_first_found_by:
                            url_first_found_by[found_url] = parser_type_str
                    
                    product_urls.update(urls)
                    logger.info(f"{parser_type_str} parser found {len(urls)} URLs on {url}")
                    
                    # If you only want to use subsequent parsers if previous ones didn't find enough:
                    if len(product_urls) >= 5:  # Adjust threshold as needed
                        break
                        
            except Exception as e:
                logger.error(f"{parser_type} parsing failed: {str(e)}")
                # Continue to the next parser
        
        # Find URLs for next depth if we're not at max depth
        next_urls = []
        if current_depth < max_depth - 1:
            next_urls = find_urls(html_content, url, domain_netloc)
            
        return product_urls, next_urls
    except Exception as e:
        logger.error(f"Error processing URL {url}: {e}")
        raise