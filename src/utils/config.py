import os
from token import OP
from dotenv import load_dotenv

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
# MongoDB Configuration (optional)
# ====================================
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "webcrawler")

# ====================================
# Storage Configuration
# ====================================
OUTPUT_DIR = "output"
SAVE_IN_JSON = True
SAVE_IN_CSV = True

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
# AI Parser Configuration
# ====================================
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_PROVIDER = "openai"
MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 1500

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
    ],
    "virgio.com": [r"/product/\d+",r"/products/\d+", r"/item/\w+", r"/p/\d+"],
    "tatacliq.com": [r"/product/.*",r"/products/\d+", r"/pdp/.*"],
    "nykaafashion.com": [r"/products/.*", r"/p/.*"],
    "westside.com": [r"/shop/.*", r"/products/.*"]
}

