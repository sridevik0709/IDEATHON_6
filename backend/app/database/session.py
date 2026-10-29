"""
Database engine and session management.
Supports PostgreSQL (via psycopg) for production and SQLite fallback for offline development.
"""

import logging
from typing import Dict, Generator, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.database.base import Base

logger = logging.getLogger("gridguard.database")

_engine: Optional[Engine] = None
_SessionFactory: Optional[sessionmaker[Session]] = None


def get_database_url() -> str:
    """Resolve database URL from settings with appropriate dialect and fallback."""
    if settings.DATABASE_URL:
        url = settings.DATABASE_URL
        # Normalize postgres:// to postgresql+psycopg:// if needed
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url
    
    # Development fallback
    if settings.DATABASE_DEV_FALLBACK_SQLITE:
        return "sqlite:///./gridguard_dev.db"
    
    return "postgresql+psycopg://postgres:postgres@localhost:5432/gridguard_nexus"


def init_database() -> Engine:
    """Initialize database engine and session factory."""
    global _engine, _SessionFactory
    db_url = get_database_url()
    is_sqlite = db_url.startswith("sqlite")

    connect_args = {"check_same_thread": False} if is_sqlite else {}

    try:
        _engine = create_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        _SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        
        # Ensure all registered tables exist
        import app.database.models  # noqa: F401 - ensure models are imported
        Base.metadata.create_all(bind=_engine)
        
        logger.info(f"Database engine initialized and schema verified with dialect: {_engine.dialect.name}")
        return _engine
    except Exception as exc:
        logger.error(f"Failed to initialize database engine: {exc}")
        raise


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        init_database()
    return _engine  # type: ignore


def SessionLocal() -> Session:
    """Convenience factory for obtaining an active session."""
    global _SessionFactory
    if _SessionFactory is None:
        init_database()
    return _SessionFactory()  # type: ignore


def get_db() -> Generator[Session, None, None]:
    """Dependency for obtaining a scoped SQLAlchemy session."""
    global _SessionFactory
    if _SessionFactory is None:
        init_database()
    session = _SessionFactory()  # type: ignore
    try:
        yield session
    finally:
        session.close()


def check_database_connection() -> Dict[str, any]:
    """
    Diagnostic probe to check database connectivity and latency.
    Safe against failures; never crashes the application.
    """
    try:
        engine = get_engine()
        dialect_name = engine.dialect.name
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "connected": True,
            "dialect": dialect_name,
            "status": "operational",
            "message": f"Connected to {dialect_name.upper()} persistent storage",
        }
    except Exception as exc:
        dialect_name = "postgresql" if settings.DATABASE_URL else "unconfigured"
        logger.warning(f"Database connection probe failed: {exc}")
        return {
            "connected": False,
            "dialect": dialect_name,
            "status": "degraded",
            "message": f"Storage connection probe failed: {str(exc).splitlines()[0]}",
        }
