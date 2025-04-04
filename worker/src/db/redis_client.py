import redis
from utils.config import REDIS_HOST, REDIS_PORT, REDIS_USERNAME, REDIS_PASSWORD

redis_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    username=REDIS_USERNAME,
    db=0,
    password=REDIS_PASSWORD,
    decode_responses=False,  # Keep binary data as is
    max_connections=20 
)

redis_client = redis.Redis(connection_pool=redis_pool)

# Expose the pool for any other clients that need it
def get_redis_client(decode_responses=False):
    """Get a Redis client using the shared connection pool"""
    return redis.Redis(
        connection_pool=redis_pool,
        decode_responses=decode_responses
    )
