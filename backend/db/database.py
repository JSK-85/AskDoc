from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

from db.models import Base

# --- Async engine (for FastAPI routes) ---
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql+asyncpg://raguser:ragpass@localhost:15432/ragdb')

async_engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)


async def create_tables():
    """Create all tables on startup."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields an async session."""
    async with AsyncSessionLocal() as session:
        yield session


# --- Sync engine (for Celery worker) ---
SYNC_DATABASE_URL = DATABASE_URL.replace('postgresql+asyncpg', 'postgresql+psycopg2')

sync_engine = create_engine(SYNC_DATABASE_URL, echo=False)
SyncSessionLocal = Session


@contextmanager
def get_sync_session():
    """Celery tasks use sync sessions."""
    session = Session(sync_engine)
    try:
        yield session
    finally:
        session.close()
