import requests
import time
from utils.logger import get_logger
from utils.config import TIMEOUT, MAX_RETRIES, USER_AGENT, CRAWL_DELAY

logger = get_logger(__name__)

def fetch_page(url: str) -> str:
    """
    Fetches a webpage content given a URL with rate limiting.
    
    Args:
    - url (str): The URL to fetch.

    Returns:
    - str: The webpage content as a string or None if failed.
    """
    logger.info(f"Fetching page: {url}")

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml",
        "Accept-Language": "en-US,en;q=0.9"
    }
    retries = 0

    # Add delay to respect server resources
    time.sleep(CRAWL_DELAY)

    while retries < MAX_RETRIES:
        try:
            response = requests.get(url, headers=headers, timeout=TIMEOUT)
            response.raise_for_status()  # Raise exception for HTTP errors
            return response.text
        except requests.RequestException as e:
            retries += 1
            logger.warning(f"Failed attempt {retries}/{MAX_RETRIES} for {url}: {e}")
            # Exponential backoff
            time.sleep(CRAWL_DELAY * (2 ** retries))

    logger.error(f"Failed to fetch {url} after {MAX_RETRIES} retries.")
    return None
