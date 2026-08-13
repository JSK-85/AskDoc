"""FastAPI application entrypoint.

Configures CORS, logging, lifespan, and mounts all route modules.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load .env file before any other imports that read env vars
load_dotenv()

from api.routes import ingest, query, health
from db.database import create_tables

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S',
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (replaces deprecated @app.on_event)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info('[startup] Creating database tables…')
    await create_tables()
    logger.info('[startup] Ready')
    yield
    logger.info('[shutdown] Goodbye')


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title='RAG Doc Q&A API', version='1.0.0', lifespan=lifespan)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:8080,http://localhost:5173')
origins = [url.strip() for url in frontend_url.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PATCH', 'DELETE', 'OPTIONS'],
    allow_headers=['Content-Type', 'X-API-KEY', 'Authorization'],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
app.include_router(health.router)
app.include_router(ingest.router, prefix='/api/v1')
app.include_router(query.router, prefix='/api/v1')
