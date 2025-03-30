from abc import ABC, abstractmethod
from typing import List
from langchain_community.chat_models import ChatOpenAI, ChatAnthropic
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
# from langchain.schema import HumanMessage, SystemMessage
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
        
        # Create a more detailed prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert web crawler specializing in e-commerce sites.
            Your task is to extract product URLs from HTML content.
            
            Guidelines:
            1. Only extract URLs that point to product pages
            2. Ensure URLs are complete and valid
            3. Remove any duplicate URLs
            4. Consider the base URL when processing relative URLs
            5. Explain your reasoning for selected URLs
            
            {format_instructions}"""),
            ("human", """Extract product URLs from this HTML content.
            Base URL: {base_url}
            HTML: {html}""")
        ])

    @abstractmethod
    def get_llm(self):
        """Get the LLM instance for the specific provider"""
        pass

    def parse(self, html: str, base_url: str) -> List[str]:
        """Parse HTML content to extract product URLs using AI."""
        try:
            # Format the prompt with the output parser instructions
            formatted_prompt = self.prompt.format_messages(
                html=html,
                base_url=base_url,
                format_instructions=self.output_parser.get_format_instructions()
            )
            
            # Get LLM response with memory
            llm = self.get_llm()
            chain = self.prompt | llm | self.output_parser
            
            # Execute the chain with memory
            result = chain.invoke({
                "html": html,
                "base_url": base_url,
                "format_instructions": self.output_parser.get_format_instructions(),
                "chat_history": self.memory.chat_memory.messages
            })
            
            # Update memory with the interaction
            self.memory.save_context(
                {"input": f"Extract URLs from {base_url}"},
                {"output": f"Found {len(result.urls)} URLs: {result.reasoning}"}
            )
            
            logger.info(f"AI parser extracted {len(result.urls)} URLs for {base_url}")
            logger.debug(f"Reasoning: {result.reasoning}")
            return result.urls
            
        except Exception as e:
            logger.error(f"AI parsing failed: {e}")
            return []

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