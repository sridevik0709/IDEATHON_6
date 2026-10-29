"""
Health-check and operational diagnostics endpoints.
"""

import time
from fastapi import APIRouter, Request
from app.accounting.placeholder import AccountingModuleStatus
from app.ai_services.placeholder import AIServicesModuleStatus
from app.config import settings
from app.core.responses import success_response
from app.data_processing.placeholder import DataProcessingModuleStatus
from app.database.session import check_database_connection
from app.schemas.common import StandardSuccessResponse
from app.schemas.health import HealthStatusData, SubsystemHealth

router = APIRouter()
_START_TIME = time.time()


@router.get(
    "/health",
    response_model=StandardSuccessResponse[HealthStatusData],
    summary="Platform Health & Diagnostics Probe",
    description="Returns platform health, uptime, persistent storage state, and subsystem readiness."
)
async def get_health(request: Request) -> StandardSuccessResponse[HealthStatusData]:
    uptime = round(time.time() - _START_TIME, 2)
    db_probe = check_database_connection()

    db_subsystem = SubsystemHealth(
        name="PostgreSQL Persistent Storage",
        status=db_probe.get("status", "disconnected"),
        details=f"{db_probe.get('message')} [Dialect: {db_probe.get('dialect')}]",
        ready=db_probe.get("connected", False)
    )

    subsystems = [
        SubsystemHealth(
            name="API & Routing Gateway",
            status="operational",
            details="FastAPI ASGI Gateway active and accepting requests",
            ready=True
        ),
        SubsystemHealth(
            name=AccountingModuleStatus.NAME,
            status=AccountingModuleStatus.STATUS,
            details=f"Phase: {AccountingModuleStatus.LEVEL_TARGET} - {AccountingModuleStatus.DESCRIPTION}",
            ready=False
        ),
        SubsystemHealth(
            name=DataProcessingModuleStatus.NAME,
            status=DataProcessingModuleStatus.STATUS,
            details=f"Phase: {DataProcessingModuleStatus.LEVEL_TARGET} - {DataProcessingModuleStatus.DESCRIPTION}",
            ready=False
        ),
        SubsystemHealth(
            name=AIServicesModuleStatus.NAME,
            status=AIServicesModuleStatus.STATUS,
            details=f"Phase: {AIServicesModuleStatus.LEVEL_TARGET} - {AIServicesModuleStatus.DESCRIPTION}",
            ready=False
        ),
    ]

    overall_status = "healthy" if db_probe.get("connected") else "operational_fallback"

    health_data = HealthStatusData(
        status=overall_status,
        project=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        stage=settings.STAGE,
        environment=settings.ENVIRONMENT,
        uptime_seconds=uptime,
        database=db_subsystem,
        subsystems=subsystems,
    )

    return success_response(data=health_data, request_id=request.headers.get("x-request-id"))
