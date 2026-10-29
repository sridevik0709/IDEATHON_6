"""
Pytest configuration and test fixtures for GridGuard Nexus X.
"""

import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))

from app.main import app
from app.config import Settings


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Synchronous test client for FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client
