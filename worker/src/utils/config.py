import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional
from constants import ParserType

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
    # Product patterns
    r'/product[s]?/[a-zA-Z0-9-_]+',  # Generic product pages
    r'/item[s]?/[a-zA-Z0-9-_]+',     # Item pages
    r'/p/[a-zA-Z0-9-_]+',            # Short product URLs
    r'/products?(?:[-/][a-zA-Z0-9-_]+)+',  # Product with categories
    r'/shop/[a-zA-Z0-9-_]+',         # Shop items
    r'/store/[^/]+/product[s]?/[a-zA-Z0-9-_]+',  # Store products
    r'/category/[^/]+/[a-zA-Z0-9-_]+',  # Category products
    r'/detail[s]?/[a-zA-Z0-9-_]+',   # Detail pages
    r'/pd[x]?/[a-zA-Z0-9-_]+',       # Product detail
    r'/buy/[a-zA-Z0-9-_]+',          # Buy pages
    r'/goods/[a-zA-Z0-9-_]+',        # Goods pages
    r'/item-[0-9]+\.html',           # Item HTML pages
    r'/[a-zA-Z0-9-_]+-p-\d+',        # Product with ID
    
    # Collection/Category patterns
    r'/collection[s]?/[a-zA-Z0-9-_]+',
    r'/category/[a-zA-Z0-9-_]+',
    r'/department/[a-zA-Z0-9-_]+',
    
    # Common e-commerce patterns
    r'/dp/[A-Z0-9]+',                # Amazon-style product
    r'/gp/product/[A-Z0-9]+',        # Alternative product format
    r'/[A-Z0-9]{10,}',              # Product IDs (like Amazon ASIN)
    
    # Query parameter patterns
    r'product_id=\d+',
    r'item_id=\d+',
    r'pid=\d+'
]

# ====================================
# Domain-specific URL Patterns
# ====================================
DOMAIN_PATTERNS = {
    "default": PATTERNS,
    "amazon": [
        r'/dp/[A-Z0-9]{10}',
        r'/gp/product/[A-Z0-9]{10}',
    ],
    "shopify": [
        r'/products/[a-zA-Z0-9-]+',
        r'/collections/[^/]+/products/[a-zA-Z0-9-]+'
    ],
    "woocommerce": [
        r'/product/[a-zA-Z0-9-]+',
        r'/shop/[a-zA-Z0-9-]+'
    ],
    "magento": [
        r'/catalog/product/view/id/\d+',
        r'/[a-zA-Z0-9-]+\.html'
    ],
    "bigcommerce": [
        r'/products/[a-zA-Z0-9-]+',
        r'/[a-zA-Z0-9-]+-p\d+'
    ]
    # Add more domain-specific patterns
}

# Pagination patterns
PAGINATION_PATTERNS = [
    r'[?&]page=\d+',
    r'[?&]p=\d+',
    r'/page/\d+',
    r'/p/\d+$',
    r'-page-\d+',
    r'_p\d+',
    r'offset=\d+',
    r'start=\d+',
    r'from=\d+'
]

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

# ====================================
# Logging Configuration
# ====================================
LOG_DIR = os.path.join(os.path.dirname(__file__), "../../Logs")
LOG_FILE = os.path.join(LOG_DIR, "worker.log")
LOG_TO_FILE = True
LOG_LEVEL_CONSOLE = "INFO"
LOG_LEVEL_FILE = "DEBUG"

# Create logs directory if it doesn't exist
if LOG_TO_FILE:
    os.makedirs(LOG_DIR, exist_ok=True)

# Define which parsers to use and in what order
PARSERS_TO_USE = [ParserType.SIMPLE, ParserType.CONFIG]

