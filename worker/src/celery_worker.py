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
    task_acks_late=True,
    # Ensure tasks with specific names are properly routed
    task_create_missing_queues=True,
    # Enable task tracking
    task_track_started=True,
)

# Import tasks module directly to ensure registration
import tasks

# Auto-discover any other tasks in the application
celery_app.autodiscover_tasks(['tasks'])

if __name__ == "__main__":
    celery_app.start()
