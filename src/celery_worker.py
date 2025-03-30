from celery import Celery
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure Celery
REDIS_URL = os.getenv("REDIS_URL")

celery_app = Celery(
    "web_crawler",
    backend=REDIS_URL,
    broker=REDIS_URL
)

celery_app.conf.update(
    result_expires=3600,  # Results expire after 1 hour
    task_serializer='json',
    accept_content=['json'],
    worker_prefetch_multiplier=1,
    task_acks_late=True
)

if __name__ == "__main__":
    celery_app.start()
