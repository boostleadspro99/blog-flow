import logging
import os
import sys
from contextlib import asynccontextmanager

# Add src/ to path for gemini_webapi imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.client_pool import GeminiClientPool

logger = logging.getLogger("app.main")

# Global pool: user_id -> GeminiClient
gemini_pool: GeminiClientPool | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global gemini_pool

    if settings.database_url:
        logger.info("Initializing database tables...")
        init_db()
        logger.info("Database tables ready.")
    else:
        logger.warning("DATABASE_URL not set — database features disabled.")

    gemini_pool = GeminiClientPool(proxy=settings.proxy or None)
    logger.info("Gemini client pool created.")

    yield

    if gemini_pool:
        await gemini_pool.close_all()
        logger.info("Gemini client pool closed.")
    close_db()


app = FastAPI(title="PuterImage Studio API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r".*",  # Reflect any origin (needed for Chrome extensions)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount routers ──
from app.routes.auth_routes import router as auth_router
from app.routes.cookies import router as cookies_router
from app.routes.images import router as images_router
from app.routes.models import router as models_router
from app.routes.proxy import router as proxy_router
from app.routes.chat import router as chat_router
from app.routes.webhook import router as webhook_router

app.include_router(auth_router)
app.include_router(cookies_router)
app.include_router(images_router)
app.include_router(models_router)
app.include_router(proxy_router)
app.include_router(chat_router)
app.include_router(webhook_router)


@app.get("/health")
async def health():
    pool_size = gemini_pool.get_active_count() if gemini_pool else 0
    return {
        "status": "ok",
        "version": "0.2.0",
        "active_clients": pool_size,
        "auth_enabled": not settings.disable_auth,
    }
