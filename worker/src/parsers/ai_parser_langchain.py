from abc import ABC, abstractmethod
from typing import List
from langchain_community.chat_models import ChatOpenAI, ChatAnthropic
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.memory import ConversationBufferMemory
from pydantic import BaseModel, Field
from utils.logger import get_logger
from utils.config import AIConfig, DEFAULT_AI_CONFIG

logger = get_logger(__name__)

class ProductURL(BaseModel):
    """Schema for product URL extraction"""
    urls: List[str] = Field(description="List of product URLs found in the HTML content")
    reasoning: str = Field(description="Brief explanation of why these URLs were selected")

class BaseAIParser(ABC):
    def __init__(self, config: AIConfig):
        self.config = config
        self.output_parser = PydanticOutputParser(pydantic_object=ProductURL)
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a specialized web scraper assistant focused on e-commerce sites. 
            Your task is to analyze HTML content and extract product URLs.

            Important considerations:
            1. Look for product URL patterns like: 
               - /product/{{id}}
               - /product-detail/{{id}}
               - /p/{{id}}
               - /item/{{id}}
               - /products/{{slug}}
               - Any URL that clearly leads to a product page
               
            2. Look for pagination links:
               - URLs with page=number parameters
               - URLs with /page/number patterns
               - Next/Previous page buttons
               
            3. Be thorough in your analysis of the HTML structure
            
            {format_instructions}
            """),
            ("human", """I need to extract all product URLs from this HTML content.
            
            Base URL: {base_url}
            
            HTML content: {html}
            
            Please analyze the HTML, find all product URLs, and explain your reasoning.
            Also note any pagination links you see that could lead to more products.
            """),
        ])

    @abstractmethod
    def get_llm(self):
        """Get the LLM instance for the specific provider"""
        pass

    def parse(self, html: str, base_url: str) -> List[str]:
        """Parse HTML content to extract product URLs using AI."""
        try:
            llm = self.get_llm()
            
            messages = list(self.memory.chat_memory.messages)
            chain_with_history = (
                self.prompt.partial(
                    chat_history=messages, 
                    format_instructions=self.output_parser.get_format_instructions()
                ) 
                | llm 
                | self.output_parser
            )
            
            result = chain_with_history.invoke({
                "html": html[:10000],
                "base_url": base_url
            })
            
            self.memory.save_context(
                {"input": f"Extract URLs from {base_url}"},
                {"output": f"Found {len(result.urls)} URLs: {result.reasoning[:100]}..."}  # Limit reasoning size in memory
            )
            
            logger.debug(f"AI parser extracted {len(result.urls)} URLs for {base_url}")
            logger.debug(f"Extraction reasoning: {result.reasoning[:200]}...")
            
            # Process URLs to ensure they're absolute
            processed_urls = self._process_urls(result.urls, base_url)
            
            return processed_urls
            
        except KeyError as e:
            logger.error(f"Missing key in AI response: {e}", exc_info=True)
            return []
        except ValueError as e:
            logger.error(f"Value error in AI parsing: {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Unexpected error in AI parsing: {e}", exc_info=True)
            return []
    
    def _process_urls(self, urls: List[str], base_url: str) -> List[str]:
        """Process extracted URLs to ensure they are absolute and unique."""
        processed = []
        seen = set()
        
        for url in urls:
            # Handle relative URLs
            if url.startswith('/'):
                base = base_url[:-1] if base_url.endswith('/') else base_url
                absolute_url = f"{base}{url}"
            elif not (url.startswith('http://') or url.startswith('https://')):
                absolute_url = f"{base_url.rstrip('/')}/{url.lstrip('/')}"
            else:
                absolute_url = url
                
            # Deduplicate URLs
            if absolute_url not in seen:
                seen.add(absolute_url)
                processed.append(absolute_url)
                
        return processed

class GoogleGeminiParser(BaseAIParser):
    def get_llm(self):
        return ChatGoogleGenerativeAI(
            model=self.config.gemini.model,
            google_api_key=self.config.gemini.api_key,
            temperature=0.1  # Lower temperature for more focused output
        )

class MistralParser(BaseAIParser):
    def get_llm(self):
        return ChatOpenAI(
            model=self.config.mistral.model,
            openai_api_key=self.config.mistral.api_key,
            openai_api_base="https://api.mistral.ai/v1",
            temperature=0.1
        )

class ClaudeParser(BaseAIParser):
    def get_llm(self):
        return ChatAnthropic(
            model=self.config.claude.model,
            anthropic_api_key=self.config.claude.api_key,
            max_tokens=self.config.claude.max_tokens,
            temperature=0.1
        )

class ChatGPTParser(BaseAIParser):
    def get_llm(self):
        return ChatOpenAI(
            model=self.config.chatgpt.model,
            openai_api_key=self.config.chatgpt.api_key,
            max_tokens=self.config.chatgpt.max_tokens,
            temperature=0.1
        )

class AIParser:
    """
    Factory class to create AI parsers based on configuration using LangChain.
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
            "claude": ClaudeParser,
            "chatgpt": ChatGPTParser
        }

        if config.provider not in parsers:
            raise ValueError(f"Unknown AI provider: {config.provider}")

        return parsers[config.provider](config) 