"""Health check endpoint that validates actual dependency connectivity."""
from fastapi import APIRouter
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('/health')
async def health():
    """Return 200 only if all critical dependencies (Postgres, Redis) are reachable."""
    checks = {}

    # --- PostgreSQL ---
    try:
        from db.database import async_engine
        from sqlalchemy import text
        async with async_engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
        checks['postgres'] = 'ok'
    except Exception as e:
        logger.error(f'[health] Postgres check failed: {e}')
        checks['postgres'] = 'error'

    # --- Redis ---
    try:
        import redis.asyncio as aioredis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = aioredis.from_url(redis_url)
        await r.ping()
        await r.aclose()
        checks['redis'] = 'ok'
    except Exception as e:
        logger.error(f'[health] Redis check failed: {e}')
        checks['redis'] = 'error'

    all_ok = all(v == 'ok' for v in checks.values())

    if all_ok:
        return {'status': 'ok', 'checks': checks}
    else:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={'status': 'degraded', 'checks': checks},
        )
