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

def get_redis_client():
    return redis.Redis(connection_pool=redis_pool)
