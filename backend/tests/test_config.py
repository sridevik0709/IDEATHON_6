"""
Unit tests for configuration loading and validation.
"""

from app.config import Settings


def test_default_settings():
    """Verify settings defaults are populated correctly."""
    s = Settings()
    assert s.PROJECT_NAME == "GRIDGUARD NEXUS X"
    assert "2.0.0" in s.PROJECT_VERSION
    assert s.PORT == 8000
    assert "http://localhost:3000" in s.CORS_ORIGINS


def test_cors_string_parsing():
    """Verify comma-separated string is parsed to a list."""
    s = Settings(CORS_ORIGINS="http://foo.com, http://bar.com")
    assert s.CORS_ORIGINS == ["http://foo.com", "http://bar.com"]
