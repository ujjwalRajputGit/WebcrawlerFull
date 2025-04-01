from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult
from tasks import crawl_task, celery_app
from utils.logger import get_logger
from db.storage import Storage
from db.redis_client import redis_client
from utils.config import (
    REDIS_HOST, REDIS_PORT, 
    CORS_ORIGINS  # Import server-specific configs
)
from urllib.parse import unquote

app = FastAPI(
    title="Web Crawler API",
    description="API for crawling e-commerce websites and extracting product URLs",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = get_logger(__name__)

@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "message": "WebCrawler API is running 🚀",
        "redis_connection": f"{REDIS_HOST}:{REDIS_PORT}"
    }

@app.post("/crawl/")
def trigger_crawl(domains: list[str], max_depth: int = 3):
    """
    Trigger the crawler for given domains.

    Args:
        domains (list): List of e-commerce domains to crawl.
        max_depth (int): Maximum crawl depth for pagination.
    
    Returns:
        dict: Celery task ID and status.
    """
    try:
        # Trigger crawl task asynchronously
        task = crawl_task.apply_async(args=[domains, max_depth])
        
        logger.info(f"Started crawling task {task.id} for domains: {domains}")
        
        return {
            "task_id": task.id,
            "status": "Crawling started",
            "domains": domains,
            "max_depth": max_depth
        }
    except Exception as e:
        logger.error(f"Error starting task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start crawl task: {str(e)}")

@app.get("/task/{task_id}")
def get_task_status(task_id: str):
    """
    Get the status of a task.
    
    Args:
        task_id (str): The ID of the task.
        
    Returns:
        dict: Task status information.
    """
    task = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task.status,
    }
    
    # Add more information based on task status
    if task.status == 'PENDING':
        response['info'] = 'Task is waiting for execution'
    elif task.status == 'STARTED':
        response['info'] = 'Task has been started'
    elif task.status == 'PROGRESS':
        response['info'] = task.info
    elif task.status == 'SUCCESS':
        response['result'] = task.result
    elif task.status == 'FAILURE':
        response['error'] = str(task.result)
    
    return response

@app.delete("/task/{task_id}")
def revoke_task(task_id: str, terminate: bool = False):
    """
    Revoke a running task.
    
    Args:
        task_id (str): Celery task ID.
        terminate (bool): Whether to terminate the task if it's running.
        
    Returns:
        dict: Result of the operation.
    """
    task = AsyncResult(task_id, app=celery_app)
    
    if task.state in ['PENDING', 'STARTED', 'RETRY']:
        task.revoke(terminate=terminate)
        return {"message": f"Task {task_id} has been revoked"}
    
    return {"message": f"Task {task_id} is already in {task.state} state and cannot be revoked"}

@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        dict: Service status information.
    """
    # Check Redis connection
    redis_status = "UP"
    try:
        redis_client.ping()
    except Exception as e:
        redis_status = f"DOWN: {str(e)}"
    
    return {
        "status": "healthy",
        "services": {
            "api": "UP",
            "redis": redis_status
        }
    }

@app.get("/urls/{task_id}/{domain:path}")
def get_urls(task_id: str, domain: str):
    """
    Get crawled URLs for a specific task and domain.
    First tries Redis, then falls back to MongoDB.
    
    Args:
        task_id (str): The ID of the crawl task
        domain (str): The domain that was crawled (can be full URL)
        
    Returns:
        dict: URLs and metadata for the domain
    """
    try:
        # Decode the URL-encoded domain
        domain = unquote(domain)
        
        # Initialize Storage class
        storage = Storage()
        
        # Try getting from Redis first
        redis_urls = storage.get_temp(domain, task_id)
        
        if redis_urls:
            logger.info(f"Found {len(redis_urls)} URLs in Redis for task {task_id}, domain {domain}")
            return {
                "source": "redis",
                "task_id": task_id,
                "domain": domain,
                "urls_count": len(redis_urls),
                "urls": redis_urls
            }
            
        # If not in Redis, try MongoDB
        mongo_result = storage.get_from_mongo(domain, task_id)
        
        if mongo_result:
            urls = mongo_result["urls"]
            logger.info(f"Found {len(urls)} URLs in MongoDB for task {task_id}, domain {domain}")
            return {
                "source": "mongodb",
                "task_id": task_id,
                "domain": domain,
                "urls_count": len(urls),
                "urls": urls,
                "timestamp": mongo_result["timestamp"]
            }
            
        # If not found in either storage
        raise HTTPException(
            status_code=404,
            detail=f"No URLs found for task {task_id} and domain {domain}"
        )
            
    except Exception as e:
        logger.error(f"Error retrieving URLs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve URLs: {str(e)}"
        )
