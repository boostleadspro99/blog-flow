"""Test database connection — catches driver/config issues before deploy."""
import os
import pytest
from dotenv import load_dotenv

load_dotenv()


def test_database_url_is_set():
    """Fail fast if DATABASE_URL is not configured."""
    url = os.getenv("DATABASE_URL")
    assert url, "DATABASE_URL is not set in environment"
    assert "://" in url, f"DATABASE_URL has no scheme: {url[:30]}..."


def test_no_double_driver(db_url):
    """Ensure the URL doesn't have double driver prefixes."""
    scheme = db_url.split("://")[0]
    parts = scheme.split("+")
    assert len(parts) <= 2, (
        f"DATABASE_URL has multiple driver prefixes: {scheme}. "
        f"Expected format: postgresql+psycopg2://..."
    )


def test_no_channel_binding(db_url):
    """channel_binding is incompatible with standard drivers."""
    if "channel_binding=require" in db_url:
        fixed = db_url.replace("&channel_binding=require", "").replace("?channel_binding=require", "")
        pytest.fail(
            f"DATABASE_URL contains 'channel_binding=require' which is incompatible.\n"
            f"Fix: remove it from the URL.\n"
            f"Suggested: {fixed}"
        )


def test_can_connect(db_url):
    """Verify we can actually connect to the database.
    This test requires valid credentials — skip in CI if DB not available."""
    from app.database import get_engine

    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.exec_driver_sql("SELECT 1")
            assert result.scalar() == 1
        engine.dispose()
    except Exception as e:
        msg = str(e)
        if "password authentication failed" in msg:
            pytest.skip(f"Skipping: database credentials need updating ({msg[:80]}...)")
        elif "could not translate host name" in msg:
            pytest.skip(f"Skipping: database host not reachable ({msg[:80]}...)")
        else:
            pytest.fail(f"Database connection failed: {msg[:200]}")
