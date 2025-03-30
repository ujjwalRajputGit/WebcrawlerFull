from fastapi import FastAPI, BackgroundTasks
from celery.result import AsyncResult
from src.tasks import crawl_task
from db import redis_client
from src.utils.logger import get_logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()
logger = get_logger(__name__)

@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "WebCrawler API is running 🚀"}

@app.post("/crawl/")
def trigger_crawl(domains: list[str], background_tasks: BackgroundTasks):
    """
    Trigger the crawler for given domains.

    Args:
        domains (list): List of e-commerce domains to crawl.
    
    Returns:
        dict: Celery task ID and status.
    """
    # Trigger crawl task asynchronously
    task = crawl_task.apply_async(args=[domains])

    logger.info(f"Started crawling task {task.id} for domains: {domains}")
    
    # Add to background task queue
    background_tasks.add_task(monitor_task_status, task.id)

    return {
        "task_id": task.id,
        "status": "Crawling started",
        "domains": domains
    }

@app.get("/status/{task_id}")
def get_task_status(task_id: str):
    """
    Get the status of a Celery task.

    Args:
        task_id (str): The Celery task ID.
    
    Returns:
        dict: Task status and result.
    """
    task = AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            "task_id": task_id,
            "status": "Pending..."
        }
    elif task.state != 'FAILURE':
        response = {
            "task_id": task_id,
            "status": task.state,
            "result": task.result
        }
    else:
        response = {
            "task_id": task_id,
            "status": "Failed",
            "error": str(task.result)
        }

    return response


def monitor_task_status(task_id: str):
    """Continuously monitor the Celery task status."""
    task = AsyncResult(task_id)

    while not task.ready():
        logger.info(f"Task {task_id} is still running...")
        redis_client.set(f"task:{task_id}:status", task.state)
    
    logger.info(f"Task {task_id} completed with status: {task.state}")






# from turtle import st
# from utils.fetcher import fetch_page
# from parsers import ParserType, get_parser
# from db.storage import Storage

# def main():

#     # url = "https://www.tatacliq.com"
#     url = "https://www.virgio.com/"
#     base_url = url
#     html_content = fetch_page(url)

#     simple_parser = get_parser(ParserType.SIMPLE)
#     config_parser = get_parser(ParserType.CONFIG)
#     ai_parser = get_parser(ParserType.AI)

#     active_parser = simple_parser
#     # active_parser = config_parser
#     active_parser = ai_parser

#     if html_content:
#         product_urls = active_parser.parse(html_content, base_url)
#         print("Extracted product URLs:")
#         if not product_urls:
#             print("No product URLs found.")
#         else:
#             for url in product_urls:
#                 print(url)
#     else:
#         print("Failed to fetch the webpage.")

#     if product_urls:
#         storage = Storage()
#         storage.save(base_url, product_urls)
#         print("Product URLs saved to storage.")


# if __name__ == "__main__":
#     main()