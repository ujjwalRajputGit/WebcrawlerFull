import requests
from utils.logger import get_logger
from utils.config import TIMEOUT, MAX_RETRIES, USER_AGENT

logger = get_logger(__name__)

def fetch_page(url: str) -> str:
    """
    Fetches a webpage content given a URL.
    
    Args:
    - url (str): The URL to fetch.

    Returns:
    - str: The webpage content as a string or None if failed.
    """
    logger.info(f"Fetching page: {url}")

    headers = {"User-Agent": USER_AGENT}
    retries = 0

    while retries < MAX_RETRIES:
        try:
            response = requests.get(url, headers=headers, timeout=TIMEOUT)
            response.raise_for_status()  # Raise exception for HTTP errors
            return response.text
        except requests.RequestException as e:
            retries += 1
            logger.warning(f"Failed attempt {retries}/{MAX_RETRIES} for {url}: {e}")

    logger.error(f"Failed to fetch {url} after {MAX_RETRIES} retries.")
    return None
