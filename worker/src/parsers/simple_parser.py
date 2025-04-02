import re
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

    def parse(self, html: str, base_url: str) -> List[str]:
        """
        Extract product URLs from the HTML content using predefined patterns.
        
        Args:
            html (str): HTML content to parse
            base_url (str): Base URL of the website
            
        Returns:
            List[str]: List of unique product URLs
        """

        urls = parse(html, base_url, self.patterns)
        logger.info(f"Simple parser extracted {len(urls)} URLs for {base_url}")
        return urls