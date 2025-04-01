import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional

# Load environment variables from .env file
load_dotenv()

# ====================================
# Redis Configuration (for async tasks)
# ====================================
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_USERNAME = os.getenv("REDIS_USERNAME", "default")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# ====================================
# MongoDB Configuration
# ====================================
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "webcrawler")

# ====================================
# Storage Configuration
# ====================================
OUTPUT_DIR = "../../output"
SAVE_IN_JSON = False
SAVE_IN_CSV = False

# ====================================
# General Crawler Configurations
# ====================================
TIMEOUT = 10  # Request timeout in seconds
MAX_RETRIES = 2  # Maximum number of retries for failed requests
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

# ====================================
# Simple Parser Configuration
# ====================================
PATTERNS = [
    r"/product/\d+",  # Generic product page
    r"/item/\d+",     # Item page
    r"/p/\d+",        # Product shortcut
    r"/products/[a-zA-Z0-9-]+",  # Slug-based products
    r"/shop/[a-zA-Z0-9-]+",      # Shop section
    r"/store/[^/]+/product/[a-zA-Z0-9-]+",  # Store-specific products
    r"/category/[^/]+/[^/]+",    # Category-based products
    r"/detail/[a-zA-Z0-9-]+",    # Detail pages
    r"/product(?:-[a-zA-Z0-9]+)+",  # Hyphen-separated product IDs
    r"/products/[0-9]+"           # Numeric product pages
]

# ====================================
# Domain-specific URL Patterns
# ====================================
DOMAIN_PATTERNS = {
    "default": [
        r"/product/\d+",  # Generic product page
        r"/item/\d+",     # Item page
        r"/p/\d+",        # Product shortcut
        r"/products/[a-zA-Z0-9-]+",  # Slug-based products
        r"/shop/[a-zA-Z0-9-]+",      # Shop section
        r"/store/[^/]+/product/[a-zA-Z0-9-]+",  # Store-specific products
        r"/category/[^/]+/[^/]+",    # Category-based products
        r"/detail/[a-zA-Z0-9-]+",    # Detail pages
        r"/product(?:-[a-zA-Z0-9]+)+",  # Hyphen-separated product IDs
        r"/products/[0-9]+"           # Numeric product pages
        r"/product-detail/\d+",   # The pattern from your example
        r"/pd/\d+",               # Common product detail
        r"/item-detail/\d+",      # Item detail
        r"/catalog/product/view/id/\d+", # Magento style
        r"/product/view/id/\d+",  # Alternative product view
        r"/productdetails/\d+"    # No hyphen variant
    ],
    "virgio.com": [r"/product/\d+",r"/products/\d+", r"/item/\w+", r"/p/\d+"],
    "tatacliq.com": [r"/product/.*",r"/products/\d+", r"/pdp/.*"],
    "nykaafashion.com": [r"/products/.*", r"/p/.*"],
    "westside.com": [r"/shop/.*", r"/products/.*"]
}


# ====================================
# AI Parser Configuration
# ====================================
@dataclass
class GeminiConfig:
    api_key: str
    model: str = "gemini-2.0-flash"

@dataclass
class MistralConfig:
    api_key: str
    model: str = "mistral-tiny"

@dataclass
class HuggingFaceConfig:
    api_key: str
    model: str = "mistralai/Mistral-7B-Instruct-v0.2"

@dataclass
class ClaudeConfig:
    api_key: str
    model: str = "claude-3-opus-20240229"
    max_tokens: int = 1000

@dataclass
class ChatGPTConfig:
    api_key: str
    model: str = "gpt-4-turbo-preview"
    max_tokens: int = 1000

@dataclass
class AIConfig:
    provider: str
    gemini: Optional[GeminiConfig] = None
    mistral: Optional[MistralConfig] = None
    huggingface: Optional[HuggingFaceConfig] = None
    claude: Optional[ClaudeConfig] = None
    chatgpt: Optional[ChatGPTConfig] = None

# AI Configuration
AI_PROVIDER = "gemini"  # Options: "gemini", "mistral", "huggingface", "claude", "chatgpt"

# Individual API Keys for each provider
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CHATGPT_API_KEY = os.getenv("CHATGPT_API_KEY", "")

# Default AI configuration
DEFAULT_AI_CONFIG = AIConfig(
    provider=AI_PROVIDER,
    gemini=GeminiConfig(api_key=GEMINI_API_KEY),
    mistral=MistralConfig(api_key=MISTRAL_API_KEY),
    huggingface=HuggingFaceConfig(api_key=HUGGINGFACE_API_KEY),
    claude=ClaudeConfig(api_key=CLAUDE_API_KEY),
    chatgpt=ChatGPTConfig(api_key=CHATGPT_API_KEY)
)

# ====================================
# Advanced Crawler Configuration
# ====================================
MAX_CRAWL_DEPTH = 3  # Maximum depth for pagination
CRAWL_DELAY = 0.5  # Delay between requests in seconds

# ====================================
# Celery Configuration
# ====================================
if REDIS_PASSWORD:
    CELERY_BROKER_URL = f"redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
    CELERY_RESULT_BACKEND = f"redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
else:
    CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
    CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

CELERY_RESULT_EXPIRES = 3600 


