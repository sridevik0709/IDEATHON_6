"""
Version and capability introspection endpoints.
"""

from fastapi import APIRouter, Request
from app.config import settings
from app.core.responses import success_response
from app.schemas.common import StandardSuccessResponse
from app.schemas.health import VersionInfoData

router = APIRouter()


@router.get(
    "/version",
    response_model=StandardSuccessResponse[VersionInfoData],
    summary="API Version and Runtime Capabilities",
    description="Returns metadata about the active platform release and capability state."
)
async def get_version(request: Request) -> StandardSuccessResponse[VersionInfoData]:
    version_data = VersionInfoData(
        project_name=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        stage=settings.STAGE,
        api_prefix=settings.API_V1_PREFIX,
        supported_protocols=["HTTP/1.1", "JSON REST", "WebSocket Ready"],
        capabilities={
            "foundation": "Active (Level 1 Foundation)",
            "request_validation": "Active (Pydantic v2)",
            "persistent_storage": "PostgreSQL (Configured / Fallback Ready)",
            "energy_accounting": "Reserved (Level 2 Milestone)",
            "telemetry_stream": "Reserved (Level 2 Milestone)",
            "ai_investigation": "Reserved (Level 3 Milestone)",
        }
    )
    return success_response(data=version_data, request_id=request.headers.get("x-request-id"))


@router.get(
    "/info",
    response_model=StandardSuccessResponse[VersionInfoData],
    summary="Platform Summary Information",
    include_in_schema=False
)
async def get_info(request: Request) -> StandardSuccessResponse[VersionInfoData]:
    return await get_version(request)
