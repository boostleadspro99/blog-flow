"""Shared test fixtures."""
import os
import sys
import pytest

# Ensure the app module is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def db_url():
    """Get DATABASE_URL from environment, skip if not set."""
    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    return url
