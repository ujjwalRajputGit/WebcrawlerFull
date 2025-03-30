import re
from parsers import pattern_parser
from urllib.parse import urlparse
from utils.logger import get_logger
from utils.config import DOMAIN_PATTERNS

logger = get_logger(__name__)

class ConfigParser:
    """
    Parses HTML content using domain-specific patterns from config.py.
    """

    def __init__(self):
        self.domain_patterns = DOMAIN_PATTERNS

    def parse(self, html:str, domain:str):
        """
        Extracts product URLs from HTML based on domain-specific patterns.

        Args:
            domain (str): The e-commerce domain being crawled.      
            html (str): The raw HTML content.

        Returns:
            list: A list of discovered product URLs.
        """

        for pattern in self.domain_patterns:
            if re.search(pattern, urlparse(domain).netloc):
                domain_pattern_key = pattern
                break
        else:
            logger.warning(f"No patterns found for domain: {domain}. Using default patterns.")
            domain_pattern_key = "default"

        patterns = self.domain_patterns.get(domain_pattern_key, None)

        logger.debug(f"Domain: {domain_pattern_key}, Patterns: {patterns}")

        return pattern_parser.parse(html, domain, patterns)





        # if domainNetlock not in self.domain_patterns:
        #     logger.warning(f"No patterns found for domain: {domain} using default patterns.")
        #     patterns = self.domain_patterns["default"]
        # else:
        #     patterns = self.domain_patterns[domain]

        urls = []

        # Extract all href links
        links = re.findall(r'href="(.*?)"', html)

        for link in links:
            for pattern in patterns:
                if re.search(pattern, link):
                    urls.append(link)

        logger.info(f"Extracted {len(urls)} URLs for {domain}.")
        return list(set(urls))  # Remove duplicates
