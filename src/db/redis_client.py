import redis
from utils.config import REDIS_HOST, REDIS_PORT, REDIS_USERNAME, REDIS_PASSWORD

# Redis connection configuration
redis_client = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    username=REDIS_USERNAME,
    password=REDIS_PASSWORD,
    db=0,
    decode_responses=False  # Use binary responses
)
