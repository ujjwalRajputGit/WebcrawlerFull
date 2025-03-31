from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from ._pattern_parser import parse
from utils.config import PATTERNS
from utils.logger import get_logger
from typing import List

logger = get_logger(__name__)

class SimpleParser:
    def __init__(self):
        """
        Initialize the SimpleParser with hardcoded URL patterns.
        """
        self.patterns = self._get_patterns()
            
        # Compile the regex patterns for better performance
        self.compiled_patterns = [re.compile(p) for p in self.patterns]

    def _get_patterns(self) -> List[str]:
        """
        Get the list of URL patterns for product detection.
        
        Returns:
            List[str]: List of URL patterns
        """

        return PATTERNS
    
        return [
            r"/product/\d+",
            r"/item/\d+",
            r"/p/\d+",
            r"/products/[a-zA-Z0-9-]+",          # Slug-based products
            r"/shop/[a-zA-Z0-9-]+",              # Shop section
            r"/store/[^/]+/product/[a-zA-Z0-9-]+",  # Store-specific products
            r"/category/[^/]+/[^/]+",            # Category-based products
            r"/detail/[a-zA-Z0-9-]+",            # Detail pages
            r"/product(?:-[a-zA-Z0-9]+)+",       # Hyphen-separated product IDs
            r"/products/[0-9]+",                 # Numeric product pages
        ]

    def parse(self, html: str, base_url: str) -> List[str]:
        """
        Extract product URLs from the HTML content using predefined patterns.
        
        Args:
            html (str): HTML content to parse
            base_url (str): Base URL of the website
            
        Returns:
            List[str]: List of unique product URLs
        """

        return parse(html, base_url, self.patterns)
    




    
        soup = BeautifulSoup(html, "html.parser")
        product_links = set()

        a_tags = soup.find_all("a", href=True)
        logger.debug(f"Found {len(a_tags)} anchor tags with href attributes.")
        
        for a_tag in a_tags:
            href = a_tag["href"]
            full_url = urljoin(base_url, href)

            logger.debug(f"Found href: {href}, Resolved URL: {full_url}")
            
            for pattern in self.compiled_patterns:
                if pattern.search(href):
                    product_links.add(full_url)
                    logger.debug(f"Matched product URL: {full_url}")
                    break

        # Normalize URLs (remove trailing slashes, duplicates)
        product_links = {url.rstrip('/') for url in product_links}
        
        logger.info(f"Extracted {len(product_links)} unique product URLs.")
        return sorted(product_links)

