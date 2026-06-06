import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

logger = logging.getLogger("app.database")


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        if not settings.database_url:
            raise RuntimeError("DATABASE_URL is not configured.")
        # Use sync engine with psycopg2 — simple, reliable, no async driver headaches
        url = (
            settings.database_url
            .replace("+asyncpg", "+psycopg2")
            .replace("+psycopg", "+psycopg2")
        )
        # Remove query params that confuse psycopg2
        for param in ("sslmode=require", "channel_binding=require"):
            url = url.replace(f"&{param}", "").replace(f"?{param}", "")
        _engine = create_engine(url, echo=False, pool_size=5, max_overflow=10)
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a sync database session."""
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured.")
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """Create all tables if they don't exist."""
    if not settings.database_url:
        logger.warning("DATABASE_URL not set, skipping table creation.")
        return
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified.")


def close_db():
    """Close the database engine."""
    global _engine, _session_factory
    if _engine:
        _engine.dispose()
        _engine = None
        _session_factory = None
