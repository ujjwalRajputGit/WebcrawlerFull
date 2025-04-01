from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult
from tasks import crawl_task, celery_app  # Import celery_app too
from db.redis_client import redis_client
from utils.logger import get_logger  # Updated import path
from utils.config import (
    REDIS_HOST, REDIS_PORT, 
    CORS_ORIGINS  # Import server-specific configs
)

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

try:
    # Test Redis connection
    redis_ping = redis_client.ping()
    logger.info(f"Redis connection test: {redis_ping}")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")

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
