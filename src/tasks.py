from celery import shared_task
from utils.fetcher import fetch_page
from parsers import config_parser, regex_parser, ai_parser
from db.storage import Storage
from utils.logger import get_logger
import time

logger = get_logger(__name__)

# Initialize Mongo and Redis storage
storage = Storage(use_redis=True, use_mongo=True)

@shared_task(bind=True)
def crawl_task(self, domains: list[str]):
    """
    Celery task for crawling multiple domains asynchronously.

    Args:
        domains (list): List of e-commerce domains.
    
    Returns:
        dict: Result of the crawl operation.
    """
    start_time = time.time()

    all_urls = {}

    for domain in domains:
        logger.info(f"🕵️‍♂️ Crawling domain: {domain}")

        try:
            html = fetch_page(domain)
            
            if not html:
                logger.warning(f"⚠️ Skipping {domain} - No HTML content.")
                continue

            # 🛠️ Use all 3 parsers
            urls_config = config_parser.parse(html)
            urls_regex = regex_parser.parse(html)
            urls_ai = ai_parser.parse(html)

            # Combine all URLs into a single set
            urls = set(urls_config + urls_regex + urls_ai)
            
            logger.info(f"✅ Found {len(urls)} URLs for {domain}")

            # Save URLs to MongoDB and Redis
            storage.store_redis(domain, list(urls))
            storage.store_mongo(domain, list(urls))

            all_urls[domain] = list(urls)

        except Exception as e:
            logger.error(f"🔥 Error crawling {domain}: {e}")

    end_time = time.time()
    duration = end_time - start_time

    logger.info(f"✅ Crawl task completed in {duration:.2f} seconds")

    return {
        "status": "completed",
        "duration": f"{duration:.2f} seconds",
        "domains": domains,
        "urls": all_urls
    }
