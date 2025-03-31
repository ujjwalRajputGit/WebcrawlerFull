from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from utils.logger import get_logger
from typing import List

logger = get_logger(__name__)

def parse(html: str, base_url: str, patterns:List[str]) -> List[str]:
    """
    Extract product URLs from the HTML content using predefined patterns.
    
    Args:
        html (str): HTML content to parse
        base_url (str): Base URL of the website
        patterns (List[str]): List of regex patterns to match product URLs
    Returns:
        List[str]: List of unique product URLs
    """

    if not patterns:
        logger.error("No patterns provided for parsing.")
        return []
    
    compiled_patterns = [re.compile(p) for p in patterns]
    logger.debug(f"Compiled {len(compiled_patterns)} regex patterns for matching.")


    soup = BeautifulSoup(html, "html.parser")
    product_links = set()
    a_tags = soup.find_all("a", href=True)
    logger.debug(f"Found {len(a_tags)} anchor tags with href attributes.")
    
    for a_tag in a_tags:
        href = a_tag["href"]
        full_url = urljoin(base_url, href)
        logger.debug(f"Found href: {href}, Resolved URL: {full_url}")
        
        for pattern in compiled_patterns:
            if pattern.search(href):
                product_links.add(full_url)
                logger.debug(f"Matched product URL: {full_url}")
                break
    # Normalize URLs (remove trailing slashes, duplicates)
    product_links = {url.rstrip('/') for url in product_links}
    
    logger.info(f"Extracted {len(product_links)} unique product URLs.")
    return sorted(product_links)