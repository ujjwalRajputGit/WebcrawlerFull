from celery import Celery
from typing import List, Dict
from utils.config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

# Create the Celery app instance with explicit backend and broker settings
celery_app = Celery(
    "web_crawler",
    backend=CELERY_RESULT_BACKEND,
    broker=CELERY_BROKER_URL
)

# Add additional configuration
celery_app.conf.update(
    result_expires=3600,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    enable_utc=True,
)

# Define the task with a consistent name
@celery_app.task(name="tasks.crawl")
def crawl_task(domains: List[str], max_depth: int = 3) -> Dict:
    """
    Task signature for crawling domains.
    The actual implementation is in the worker project.
    
    Args:
        domains (list): List of e-commerce domains.
        max_depth (int): Maximum crawl depth for pagination.
    
    Returns:
        dict: Result of the crawl operation.
    """
    # This is just a task signature used by the server to call the worker
    pass