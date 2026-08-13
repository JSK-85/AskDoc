"""API dependencies: authentication and rate limiting."""
from fastapi import Header, HTTPException, Request
import os
import time
import logging
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


async def verify_api_key(request: Request, x_api_key: str | None = Header(None)):
    key = x_api_key or request.query_params.get("api_key")
    if key != os.getenv('API_KEY'):
        raise HTTPException(status_code=401, detail='Unauthorized')


# ---------------------------------------------------------------------------
# Redis-backed rate limiter (survives restarts, works across workers/pods)
# ---------------------------------------------------------------------------
_redis_pool: aioredis.Redis | None = None


def _get_redis() -> aioredis.Redis:
    """Lazy-init a shared async Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        _redis_pool = aioredis.from_url(redis_url, decode_responses=True)
    return _redis_pool


class RateLimit:
    """FastAPI Dependency — Redis sliding-window rate limiter.

    Falls back to allowing requests if Redis is unavailable.
    """

    def __init__(self, limit: int = 10, window: int = 60):
        self.limit = limit
        self.window = window

    async def __call__(self, request: Request):
        client_ip = request.client.host if request.client else 'unknown'
        api_key = request.headers.get('x-api-key', client_ip)
        rate_key = f'rl:{api_key}'

        try:
            r = _get_redis()
            pipe = r.pipeline(transaction=True)
            now = time.time()
            window_start = now - self.window

            # Remove entries outside the window, add current, count
            pipe.zremrangebyscore(rate_key, '-inf', window_start)
            pipe.zadd(rate_key, {str(now): now})
            pipe.zcard(rate_key)
            pipe.expire(rate_key, self.window)
            results = await pipe.execute()

            count = results[2]
            if count > self.limit:
                raise HTTPException(
                    status_code=429,
                    detail='Too many requests. Please try again later.',
                )
        except HTTPException:
            raise
        except Exception as e:
            # Redis down → degrade gracefully, allow the request
            logger.warning(f'[rate-limit] Redis unavailable, allowing request: {e}')
