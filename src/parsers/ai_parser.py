import tldextract
from bs4 import BeautifulSoup
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from utils.config import LLM_API_KEY
from utils.logger import get_logger

logger = get_logger(__name__)

class AIParser:
    """
    AI-based HTML parser using LLMs and NLP techniques.
    """
    def __init__(self):
        self.openai_api_key = LLM_API_KEY
        if not self.openai_api_key:
            logger.error("LLM API key is not set.")
        self.llm = ChatOpenAI(model_name="gpt-4", temperature=0, openai_api_key=self.openai_api_key)

    def parse(self, html: str, domain: str):
        """
        Extract product URLs using LLM-based HTML parsing.

        Args:
            html (str): HTML content of the webpage.
            domain (str): Target domain.

        Returns:
            list: List of product URLs.
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Extract all href links
            all_links = [a['href'] for a in soup.find_all('a', href=True)]
            logger.info(f"Extracted {len(all_links)} links using BeautifulSoup")

            # Filter valid URLs
            valid_urls = self.filter_urls(all_links, domain)

            # Use LLM to classify valid product URLs
            prompt = PromptTemplate(
                input_variables=["urls", "domain"],
                template="""
                You are a web crawler specializing in e-commerce sites. 
                Identify which of the following URLs are product or category pages. 
                Return only the valid product or category URLs, one per line.

                Domain: {domain}
                URLs:
                {urls}
                """
            )

            llm_input = prompt.format(urls="\n".join(valid_urls), domain=domain)
            response = self.llm.predict(llm_input)

            # Extract URLs returned by LLM
            llm_urls = response.split("\n")
            llm_urls = [url.strip() for url in llm_urls if url.strip()]

            logger.info(f"LLM filtered {len(llm_urls)} product URLs.")
            return llm_urls

        except Exception as e:
            logger.error(f"AI parsing failed: {e}")
            return []

    def filter_urls(self, urls, domain):
        """
        Filter URLs to keep only the valid ones belonging to the target domain.

        Args:
            urls (list): List of extracted URLs.
            domain (str): Target domain.

        Returns:
            list: Filtered list of valid URLs.
        """
        valid_urls = []
        domain_ext = tldextract.extract(domain)

        for url in urls:
            # Normalize URLs
            if url.startswith("//"):
                url = f"https:{url}"
            elif url.startswith("/"):
                url = f"https://{domain}{url}"

            # Validate domain
            extracted = tldextract.extract(url)
            if extracted.domain == domain_ext.domain:
                valid_urls.append(url)

        logger.info(f"Filtered {len(valid_urls)} valid URLs for {domain}.")
        return valid_urls
