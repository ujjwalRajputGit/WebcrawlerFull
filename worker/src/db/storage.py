import csv
import json
from typing import List

from utils.config import OUTPUT_DIR, SAVE_IN_JSON, SAVE_IN_CSV
from db.redis_client import redis_client
from db.mongo_client import db
from utils.logger import get_logger
from datetime import datetime
from tldextract import extract

logger = get_logger(__name__)

class Storage:
    """
    Handles the storage of crawled URLs in Redis, MongoDB, and file outputs.
    """

    def __init__(self, redis_expire=86400):
        """
        Initialize storage with Redis and MongoDB clients.
        
        Args:
            redis_expire (int): Expiry time for Redis keys in seconds.
        """
        self.redis_expire = redis_expire
        if not OUTPUT_DIR:
            raise ValueError("Output directory is not set. Please set OUTPUT_DIR in config.py.")
        self.output_dir = OUTPUT_DIR

    def save(self, domain, taskId, urls):
        """
        Save the final product URLs to Redis, MongoDB, and files.
        
        Args:
            domain (str): The domain being crawled.
            urls (list): List of discovered product URLs.
        """

        self.store_temp(domain, taskId, urls)
        self.store_mongo(domain, taskId, urls)

        if SAVE_IN_JSON:
            self.save_to_json(domain, taskId, urls)
        
        if SAVE_IN_CSV:
            self.save_to_csv(domain, taskId, urls)

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
        # Use the domain as the unique ID
        return f"{parsed_url.domain}.{parsed_url.suffix}".replace(".", "_")
    
    def _get_redis_key(self, domain, taskId):
        """
        Generate a Redis key based on the domain.
        
        Args:
            domain (str): The domain being crawled.

        Returns:
            str: The Redis key.
        """
        # Use a single key for all domains
        return f"{self._get_root_name()}:{taskId}:{self._simplify_domain(domain)}"

    def _get_mongo_collection_name(self):
        """
        Generate a MongoDB collection name based on the domain.
        
        Args:
            domain (str): The domain being crawled.

        Returns:
            str: The MongoDB collection name.
        """
        # Use a single collection for all domains
        return self._get_root_name()
    
    
    def _get_file_name(self, domain, taskId, file_type):
        """
        Generate a file name based on the domain and file type.
        
        Args:
            domain (str): The domain being crawled.
            file_type (str): The type of file (json or csv).

        Returns:
            str: The file name.
        """
        return f"{self._simplify_domain(domain)}-{taskId}.{file_type}"

    ## Store URLs temporarily in Redis
    def store_temp(self, domain, taskId, urls):
        """
        Store URLs temporarily in Redis to prevent duplicates.
        
        Args:
            domain (str): The domain being crawled.
            urls (list): List of discovered product URLs.
        """

        redis_key = self._get_redis_key(domain, taskId)

        for url in urls:
            redis_client.sadd(redis_key, url)
            redis_client.expire(redis_key, self.redis_expire)

        logger.info(f"Stored {len(urls)} URLs in Redis for {domain}.")

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

    ## Store URLs in MongoDB
    def store_mongo(self, domain, taskId, urls):
        """
        Store URLs in MongoDB using one document per domain with URL array.

        Args:
            domain (str): The domain being crawled.
            urls (list): List of discovered product URLs.
        """

        # Use a single collection for all domains
        collection = db[self._get_mongo_collection_name()]

        try:
            documet_id = taskId

            # Check if the domain document already exists
            existing_doc = collection.find_one({"_id": documet_id, "domain": self._simplify_domain(domain)})

            if existing_doc:
                # Combine new URLs with existing ones, avoiding duplicates
                existing_urls = set(existing_doc.get("urls", []))
                new_urls = set(urls)

                combined_urls = list(existing_urls.union(new_urls))

                # Update the document with combined URLs
                collection.update_one(
                    {"_id": documet_id},
                    {
                        "$set": {
                            "urls": combined_urls,
                            "timestamp": datetime.utcnow()
                        }
                    }
                )
                logger.info(f"Updated {len(new_urls)} new URLs for {documet_id} in MongoDB.")
            else:
                # Create new document if it doesn't exist
                collection.insert_one({
                    "_id": documet_id,
                    "domain": self._simplify_domain(domain),
                    "urls": urls,
                    "timestamp": datetime.now()
                })
                logger.info(f"Inserted {len(urls)} URLs for {domain} in MongoDB.")

        except Exception as e:
            logger.error(f"Failed to store URLs in MongoDB: {e}")

    ## Save to JSON
    def save_to_json(self, domain, taskId, urls):
        """
        Save the final product URLs to a JSON file.

        Args:
            domain (str): The domain being crawled.
            urls (list): List of discovered product URLs.
            output_dir (str): Directory to save the file.
        """
        filename = self._get_file_name(domain, taskId, "json")
        filepath = f"{self.output_dir}/{filename}"
        
        with open(filepath, "a") as file:
            json.dump(urls, file, indent=4)

        logger.info(f"Saved {len(urls)} URLs to {filepath}.")

    ## Save to CSV
    def save_to_csv(self, domain, taskId, urls):
        """
        Save the final product URLs to a CSV file.

        Args:
            domain (str): The domain being crawled.
            urls (list): List of discovered product URLs.
            output_dir (str): Directory to save the file.
        """
        filename = self._get_file_name(domain, taskId, "csv")
        filepath = f"{self.output_dir}/{filename}"

        with open(filepath, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["URL"])
            for url in urls:
                writer.writerow([url])

        logger.info(f"Saved {len(urls)} URLs to {filepath}.")

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
                logger.info(f"Retrieved {len(urls)} URLs from MongoDB for {domain}")
                return {
                    "urls": urls,
                    "timestamp": timestamp
                }
            
            logger.info(f"No URLs found in MongoDB for {domain}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve URLs from MongoDB: {e}")
            return None
