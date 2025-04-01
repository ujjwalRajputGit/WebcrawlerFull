import os
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
# MongoDB Configuration
# ====================================
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "webcrawler")

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
# App Configuration
# ====================================
CORS_ORIGINS = "http://localhost:3000"