from typing import List
from db.redis_client import redis_client
from db.mongo_client import db
from utils.logger import get_logger
from tldextract import extract

logger = get_logger(__name__)

class Storage:
    """
    Handles the storage of crawled URLs in Redis, MongoDB, and file outputs.
    """

    def __init__(self):
        pass


    def _get_root_name(self):
        return "crawler_urls"
    
    def _simplify_domain(self, domain):
        """
        Generate a unique ID based on the domain.
        
        Args:
            domain (str): The domain being crawled.

        Returns:
            str: The unique ID for the domain.
        """
        parsed_url = extract(domain)
        logger.debug(f"Parsed URL: {parsed_url}")
        logger.debug(f"Simplifying domain: {domain} to {parsed_url.domain}.{parsed_url.suffix}")
        return f"{parsed_url.domain}.{parsed_url.suffix}".replace(".", "_")
    
    def _get_redis_key(self, domain, taskId):
        """
        Generate a Redis key based on the domain.
        
        Args:
            domain (str): The domain being crawled.

        Returns:
            str: The Redis key.
        """
        return f"{self._get_root_name()}:{taskId}:{self._simplify_domain(domain)}"

    def _get_mongo_collection_name(self):
        """
        Generate a MongoDB collection name based on the domain.
        
        Args:
            domain (str): The domain being crawled.

        Returns:
            str: The MongoDB collection name.
        """
        return self._get_root_name()

    ## Retrieve URLs from Redis
    def get_temp(self, domain, taskId):
        """
        Get the list of URLs from Redis.

        Args:
            domain (str): The domain being crawled.

        Returns:
            list: List of URLs stored in Redis.
        """
        redis_key = self._get_redis_key(domain, taskId)
        urls = redis_client.smembers(redis_key)
        return [url.decode('utf-8') for url in urls]

    def get_from_mongo(self, domain: str, task_id: str) -> List[str]:
        """
        Get URLs from MongoDB for a specific domain and task.
        
        Args:
            domain (str): The domain being crawled
            task_id (str): The ID of the task
            
        Returns:
            List[str]: List of URLs stored in MongoDB
        """
        try:
            collection = db[self._get_mongo_collection_name()]
            simplified_domain = self._simplify_domain(domain)
            
            mongo_doc = collection.find_one({
                "_id": task_id,
                "domain": simplified_domain
            })
            
            if mongo_doc:
                urls = mongo_doc.get("urls", [])
                timestamp = mongo_doc.get("timestamp")
                logger.debug(f"Retrieved {len(urls)} URLs from MongoDB for task {task_id}, domain {domain} and simplified domain {simplified_domain}")
                return {
                    "urls": urls,
                    "timestamp": timestamp
                }
            
            logger.debug(f"No URLs found in MongoDB for task {task_id}, domain {domain} and simplified domain {simplified_domain}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve URLs from MongoDB: {e}")
            return None
