from celery import shared_task
from typing import List, Dict

# Define task signatures that are shared between server and worker
@shared_task(bind=True)
def crawl_task(self, domains: List[str], max_depth: int = 3) -> Dict:
    """
    Task signature for crawling domains - implementation is on the worker server.
    
    Args:
        domains (list): List of e-commerce domains.
        max_depth (int): Maximum crawl depth for pagination.
    
    Returns:
        dict: Result of the crawl operation.
    """
    # Implementation is in worker/tasks.py
    pass 