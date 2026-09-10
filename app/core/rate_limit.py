import logging
import uuid
from functools import lru_cache

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

RATE_LIMIT_WINDOW_SECONDS = 3600


@lru_cache
def get_redis_client() -> redis.Redis:
    return redis.from_url(get_settings().redis_url)

#todo understand this 
async def is_rate_limited(conversation_id: uuid.UUID) -> bool:
    key = f"ratelimit:conversation:{conversation_id}"
    try:
        client = get_redis_client()
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, RATE_LIMIT_WINDOW_SECONDS)
        return count > get_settings().rate_limit_max_per_hour
    except RedisError:
        logger.warning("redis unreachable — rate limiting disabled for this check", exc_info=True)
        return False
