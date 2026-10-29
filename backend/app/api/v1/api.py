"""
Aggregated API v1 Router.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health, validation, version

api_v1_router = APIRouter()

api_v1_router.include_router(health.router, tags=["Health & Diagnostics"])
api_v1_router.include_router(version.router, tags=["Version & Platform"])
api_v1_router.include_router(validation.router, tags=["Request Validation & Error Verification"])
