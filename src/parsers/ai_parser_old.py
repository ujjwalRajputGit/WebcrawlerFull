from abc import ABC, abstractmethod
from typing import List
import google.generativeai as genai
from mistralai.client import MistralClient
from huggingface_hub import InferenceClient
from anthropic import Anthropic
from openai import OpenAI
from utils.logger import get_logger
from utils.config import AIConfig, DEFAULT_AI_CONFIG

logger = get_logger(__name__)

class BaseAIParser(ABC):
    @abstractmethod
    def parse(self, html: str, base_url: str) -> List[str]:
        """Extract product URLs using AI."""
        pass

class GoogleGeminiParser(BaseAIParser):
    def __init__(self, config):
        genai.configure(api_key=config.gemini.api_key)
        self.model = genai.GenerativeModel(config.gemini.model)

    def parse(self, html: str, base_url: str) -> List[str]:
        prompt = f"""Extract product URLs from this HTML content. Base URL: {base_url}
        Return only the URLs, one per line.
        HTML: {html}"""
        
        response = self.model.generate_content(prompt)
        return [url.strip() for url in response.text.split('\n') if url.strip()]

class MistralParser(BaseAIParser):
    def __init__(self, config):
        self.client = MistralClient(api_key=config.mistral.api_key)
        self.model = config.mistral.model

    def parse(self, html: str, base_url: str) -> List[str]:
        messages = [
            {"role": "user", "content": f"Extract product URLs from this HTML content. Base URL: {base_url}. Return only the URLs, one per line. HTML: {html}"}
            ]
        response = self.client.chat(model=self.model, messages=messages)
        return [url.strip() for url in response.choices[0].message.content.split('\n') if url.strip()]

class HuggingFaceParser(BaseAIParser):
    def __init__(self, config):
        self.client = InferenceClient(token=config.huggingface.api_key)
        self.model = config.huggingface.model

    def parse(self, html: str, base_url: str) -> List[str]:
        prompt = f"""Extract product URLs from this HTML content. Base URL: {base_url}
        Return only the URLs, one per line.
        HTML: {html}"""
        
        response = self.client.text_generation(prompt, model=self.model)
        return [url.strip() for url in response.split('\n') if url.strip()]

class ClaudeParser(BaseAIParser):
    def __init__(self, config):
        self.client = Anthropic(api_key=config.claude.api_key)
        self.model = config.claude.model
        self.max_tokens = config.claude.max_tokens

    def parse(self, html: str, base_url: str) -> List[str]:
        prompt = f"""Extract product URLs from this HTML content. Base URL: {base_url}
        Return only the URLs, one per line.
        HTML: {html}"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return [url.strip() for url in response.content[0].text.split('\n') if url.strip()]

class ChatGPTParser(BaseAIParser):
    def __init__(self, config):
        self.client = OpenAI(api_key=config.chatgpt.api_key)
        self.model = config.chatgpt.model
        self.max_tokens = config.chatgpt.max_tokens

    def parse(self, html: str, base_url: str) -> List[str]:
        prompt = f"""Extract product URLs from this HTML content. Base URL: {base_url}
        Return only the URLs, one per line.
        HTML: {html}"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return [url.strip() for url in response.choices[0].message.content.split('\n') if url.strip()]

class AIParser:
    """
    Factory class to create AI parsers based on configuration.
    """
    def __init__(self):
        self.config = DEFAULT_AI_CONFIG
        self.parser = self._get_ai_parser(self.config)

    def parse(self, html: str, base_url: str) -> List[str]:
        """
        Parse HTML content using the selected AI parser.
        
        Args:
            html (str): HTML content to parse
            base_url (str): Base URL of the website
            
        Returns:
            List[str]: List of unique product URLs
        """
        return self.parser.parse(html, base_url)
    

    def _get_ai_parser(self, config: AIConfig) -> BaseAIParser:
        """Factory function to get the appropriate AI parser based on configuration."""
        parsers = {
            "gemini": GoogleGeminiParser,
            "mistral": MistralParser,
            "huggingface": HuggingFaceParser,
            "claude": ClaudeParser,
            "chatgpt": ChatGPTParser
        }

        if config.provider not in parsers:
            raise ValueError(f"Unknown AI provider: {config.provider}")

        return parsers[config.provider](config)

