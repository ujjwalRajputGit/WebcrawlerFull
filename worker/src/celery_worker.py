from celery import Celery
from utils.config import (
    CELERY_BROKER_URL, 
    CELERY_RESULT_BACKEND,
    CELERY_RESULT_EXPIRES
)

# Create Celery app with configuration from config.py
celery_app = Celery(
    "web_crawler",
    backend=CELERY_RESULT_BACKEND,
    broker=CELERY_BROKER_URL
)

# Apply configuration from config.py
celery_app.conf.update(
    result_expires=CELERY_RESULT_EXPIRES,
    task_serializer='json',
    accept_content=['json'],
    worker_prefetch_multiplier=1,
    task_acks_late=True
)

# Auto-discover tasks in the worker directory
celery_app.autodiscover_tasks()

if __name__ == "__main__":
    celery_app.start()
