"""
Main FastAPI application entrypoint for GridGuard Nexus X.
Level 1: Project Foundation.
"""

from contextlib import asynccontextmanager
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.router import api_router
from app.config import settings
from app.core.handlers import register_exception_handlers
from app.database.session import check_database_connection, init_database

# Configure logging format
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("gridguard.nexus")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    logger.info("================================================================")
    logger.info(f"Starting {settings.PROJECT_NAME} [{settings.STAGE}]")
    logger.info(f"Version: {settings.PROJECT_VERSION} | Environment: {settings.ENVIRONMENT}")
    logger.info(f"CORS Allowed Origins: {settings.CORS_ORIGINS}")
    logger.info("================================================================")

    # Initialize persistent storage connection
    try:
        init_database()
        db_status = check_database_connection()
        logger.info(f"Storage Initialization: {db_status.get('message')}")
    except Exception as exc:
        logger.warning(f"Database initialization warning: {exc}")

    yield

    logger.info(f"Shutting down {settings.PROJECT_NAME} gracefully.")


def create_application() -> FastAPI:
    """Application factory for GridGuard Nexus X."""
    app = FastAPI(
        title=f"{settings.PROJECT_NAME} - Backend API",
        version=settings.PROJECT_VERSION,
        description=(
            "GridGuard Nexus X: High-integrity electricity intelligence and investigation platform. "
            "Level 1: Foundation Services."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS for frontend access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Middleware: Request ID and execution timing
    @app.middleware("http")
    async def add_process_time_and_request_id(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = (time.time() - start_time) * 1000
        response.headers["x-request-id"] = request_id
        response.headers["x-process-time-ms"] = f"{process_time:.2f}"
        return response

    # Register centralized consistent exception handlers
    register_exception_handlers(app)

    # Mount API routes
    app.include_router(api_router)

    # Convenience root redirects
    @app.get("/", include_in_schema=False)
    async def root_redirect():
        return RedirectResponse(url="/api/v1/health")

    @app.get("/health", include_in_schema=False)
    async def top_level_health():
        return RedirectResponse(url="/api/v1/health")

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
