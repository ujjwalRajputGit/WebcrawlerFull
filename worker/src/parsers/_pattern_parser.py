from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from utils.logger import get_logger
from typing import List

logger = get_logger(__name__)

def parse(html: str, base_url: str, patterns: List[str]) -> List[str]:
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
    soup = BeautifulSoup(html, "html.parser")
    product_links = set()
    
    a_tags = soup.find_all("a", href=True)
    logger.debug(f"Found {len(a_tags)} anchor tags with href attributes.")
    
    for a_tag in a_tags:
        href = a_tag["href"]
        full_url = urljoin(base_url, href)
        
        if any(pattern.search(full_url) for pattern in compiled_patterns):
            product_links.add(full_url.rstrip('/'))
    
    logger.info(f"Extracted {len(product_links)} unique product URLs for {base_url}")
    return sorted(product_links)

# def parse(html: str, base_url: str, patterns: List[str]) -> List[str]:
#     """
#     Extract product URLs from the HTML content using predefined patterns without compiling them.
    
#     Args:
#         html (str): HTML content to parse
#         base_url (str): Base URL of the website
#         patterns (List[str]): List of regex patterns to match product URLs
#     Returns:
#         List[str]: List of unique product URLs
#     """
#     if not patterns:
#         logger.error("No patterns provided for parsing.")
#         return []
    
#     soup = BeautifulSoup(html, "html.parser")
#     product_links = set()
    
#     a_tags = soup.find_all("a", href=True)
#     logger.debug(f"Found {len(a_tags)} anchor tags with href attributes.")
    
#     for a_tag in a_tags:
#         href = a_tag["href"]
#         full_url = urljoin(base_url, href)
        
#         # Directly use patterns without compiling
#         if any(re.search(pattern, full_url) for pattern in patterns):
#             product_links.add(full_url.rstrip('/'))
    
#     logger.info(f"Extracted {len(product_links)} unique product URLs for {base_url}")
#     return sorted(product_links)