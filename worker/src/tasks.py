from tasks_signature import crawl_task
from utils.fetcher import fetch_page
from parsers import ParserType, get_parser
from db.storage import Storage
from utils.logger import get_logger
import time
from urllib.parse import urlparse
from typing import Set, Dict, List

logger = get_logger(__name__)

# Initialize storage
storage = Storage()

@crawl_task.app.task(bind=True, name=crawl_task.name)
def crawl_task_impl(self, domains: List[str], max_depth: int = 3) -> Dict:
    """
    Implementation of the crawl_task.
    This replaces the placeholder in worker/tasks_signature.py.
    """
    start_time = time.time()
    all_urls = {}

    # Initialize all three parsers
    simple_parser = get_parser(ParserType.SIMPLE)
    config_parser = get_parser(ParserType.CONFIG) 
    ai_parser = get_parser(ParserType.AI)

    for domain in domains:
        logger.info(f"🕵️‍♂️ Starting deep crawl for domain: {domain}")
        
        # Track visited URLs to avoid duplicates
        visited_urls = set()
        urls_to_visit = [domain]
        
        # Store all discovered product URLs for this domain
        domain_product_urls = set()
        
        # Extract domain for checking internal links
        domain_netloc = urlparse(domain).netloc
        
        # Control crawl depth
        current_depth = 0
        
        while urls_to_visit and current_depth < max_depth:
            current_batch = urls_to_visit.copy()
            urls_to_visit = []
            
            logger.info(f"Crawling depth {current_depth}: Processing {len(current_batch)} URLs")
            
            for url in current_batch:
                if url in visited_urls:
                    continue
                    
                try:
                    logger.info(f"Fetching page: {url}")
                    html = fetch_page(url)
                    visited_urls.add(url)
                    
                    if not html:
                        logger.warning(f"⚠️ No HTML content for {url}, skipping.")
                        continue
                    
                    # Use all three parsers to extract product URLs
                    urls_simple = simple_parser.parse(html, url)
                    urls_config = config_parser.parse(html, url)
                    urls_ai = ai_parser.parse(html, url)
                    
                    # Combine all results
                    product_urls = set(urls_simple + urls_config + urls_ai)
                    
                    if product_urls:
                        domain_product_urls.update(product_urls)
                        logger.info(f"Found {len(product_urls)} product URLs on {url}")
                        
                    # Generate and add sequential product URLs based on discovered patterns
                    sequential_urls = generate_sequential_urls(product_urls)
                    if sequential_urls:
                        domain_product_urls.update(sequential_urls)
                        logger.info(f"Generated {len(sequential_urls)} additional sequential URLs")
                    
                    # Look for pagination links
                    pagination_urls = find_pagination_links(html, url, domain_netloc)
                    
                    # Add pagination URLs to visit queue for next depth
                    for pagination_url in pagination_urls:
                        if pagination_url not in visited_urls:
                            urls_to_visit.append(pagination_url)
                    
                    logger.info(f"Found {len(pagination_urls)} pagination links to follow")
                    
                except Exception as e:
                    logger.error(f"🔥 Error crawling {url}: {e}")
            
            # Move to next depth
            current_depth += 1
            
            # Periodically save URLs to avoid data loss
            if domain_product_urls:
                storage.save(domain, list(domain_product_urls))
                logger.info(f"Saved {len(domain_product_urls)} URLs at depth {current_depth}")
        
        # Final report
        if domain_product_urls:
            logger.info(f"✅ Total unique product URLs for {domain}: {len(domain_product_urls)}")
            all_urls[domain] = list(domain_product_urls)
        else:
            logger.warning(f"No product URLs found for {domain}")

    end_time = time.time()
    duration = end_time - start_time

    logger.info(f"✅ Deep crawl completed in {duration:.2f} seconds")

    return {
        "status": "completed",
        "duration": f"{duration:.2f} seconds",
        "domains": domains,
        "urls_count": {domain: len(urls) for domain, urls in all_urls.items()},
        "total_urls": sum(len(urls) for urls in all_urls.values())
    }

def find_pagination_links(html: str, base_url: str, domain_netloc: str) -> List[str]:
    """
    Extract pagination links from HTML content.
    
    Args:
        html (str): HTML content to parse
        base_url (str): Base URL of the page
        domain_netloc (str): Domain netloc to filter internal links
        
    Returns:
        List[str]: List of pagination URLs
    """
    from bs4 import BeautifulSoup
    import re
    from urllib.parse import urljoin, urlparse
    
    soup = BeautifulSoup(html, "html.parser")
    pagination_links = set()
    
    # Common pagination patterns
    pagination_patterns = [
        r'[?&]page=\d+',
        r'[?&]p=\d+',
        r'/page/\d+',
        r'[?&]offset=\d+',
        r'[?&]start=\d+'
    ]
    
    # Find pagination elements by common class names
    pagination_classes = [
        'pagination', 'pager', 'pages', 'page-numbers', 
        'paginate', 'paging', 'page-link', 'page-item'
    ]
    
    # Look for elements with pagination classes
    for class_name in pagination_classes:
        for element in soup.find_all(class_=lambda x: x and class_name in x.lower()):
            for a_tag in element.find_all('a', href=True):
                href = a_tag['href']
                full_url = urljoin(base_url, href)
                
                # Only include internal links
                if urlparse(full_url).netloc == domain_netloc:
                    for pattern in pagination_patterns:
                        if re.search(pattern, href):
                            pagination_links.add(full_url)
                            break
    
    # Also find direct links with pagination patterns
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        
        # Check if the link text suggests pagination (numbers, next, prev)
        text = a_tag.get_text().strip().lower()
        if text.isdigit() or text in ['next', 'prev', 'previous', '>>', '<<']:
            full_url = urljoin(base_url, href)
            
            # Only include internal links
            if urlparse(full_url).netloc == domain_netloc:
                pagination_links.add(full_url)
                continue
        
        # Check against patterns
        for pattern in pagination_patterns:
            if re.search(pattern, href):
                full_url = urljoin(base_url, href)
                
                # Only include internal links
                if urlparse(full_url).netloc == domain_netloc:
                    pagination_links.add(full_url)
                    break
    
    return list(pagination_links)

def generate_sequential_urls(product_urls: Set[str]) -> Set[str]:
    """
    Generate adjacent product URLs based on numeric patterns.
    
    Args:
        product_urls (Set[str]): Set of discovered product URLs
    
    Returns:
        Set[str]: Additional generated product URLs
    """
    import re
    
    additional_urls = set()
    
    # Find URLs with numeric IDs
    for url in product_urls:
        # Look for patterns like /product-detail/12345
        match = re.search(r'(/[^/]+/(\d+))(?:/|$)', url)
        if match:
            path_prefix = url[:url.find(match.group(1))]
            id_part = match.group(2)
            try:
                product_id = int(id_part)
                # Generate URLs with IDs ±10 of the found ID
                range_start = max(1, product_id - 10)
                range_end = product_id + 10
                
                for new_id in range(range_start, range_end + 1):
                    if str(new_id) != id_part:  # Skip the original ID
                        new_url = f"{path_prefix}{match.group(1).replace(id_part, str(new_id))}"
                        additional_urls.add(new_url)
            except ValueError:
                continue
    
    return additional_urls
