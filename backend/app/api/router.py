"""
Top-level API router for versioning.
"""

from fastapi import APIRouter
from app.api.v1.api import api_v1_router
from app.config import settings

api_router = APIRouter()
api_router.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
