"""
Request validation and error consistency endpoints.
Demonstrates Pydantic schema validation and standard error response compliance.
"""

from fastapi import APIRouter, Query, Request
from app.core.exceptions import (
    ConfigurationException,
    DatabaseUnavailableException,
    ResourceNotFoundException,
    ValidationFailedException,
)
from app.core.responses import success_response
from app.schemas.common import StandardSuccessResponse
from app.schemas.health import ValidationProbeRequest, ValidationProbeResponse

router = APIRouter()


@router.post(
    "/validate/telemetry-envelope",
    response_model=StandardSuccessResponse[ValidationProbeResponse],
    summary="Validate Telemetry Envelope",
    description="Validates incoming electrical telemetry metadata against strict Pydantic rules."
)
async def validate_telemetry_envelope(
    payload: ValidationProbeRequest,
    request: Request
) -> StandardSuccessResponse[ValidationProbeResponse]:
    # Determine frequency band
    nominal_band = "50Hz Standard (e.g. India / Europe / UK)" if 48.0 <= payload.grid_frequency_hz <= 52.0 else "60Hz Standard (e.g. Americas)"
    
    # Determine voltage tier
    if payload.voltage_rms <= 1000:
        voltage_class = "Low Voltage (LV Distribution)"
    elif payload.voltage_rms <= 33000:
        voltage_class = "Medium Voltage (MV Substation)"
    else:
        voltage_class = "Extra High Voltage (EHV Transmission)"

    response_data = ValidationProbeResponse(
        valid=True,
        received_station=payload.station_id.upper(),
        nominal_band=nominal_band,
        voltage_class=voltage_class,
    )
    return success_response(data=response_data, request_id=request.headers.get("x-request-id"))


@router.get(
    "/simulate-error",
    summary="Simulate Standardized Error Responses",
    description="Diagnostic endpoint demonstrating 100% consistent error structures across status codes."
)
async def simulate_error(
    scenario: str = Query(
        "not_found",
        description="Scenario to simulate: 'not_found', 'validation', 'database', 'config', or 'unhandled'"
    )
):
    if scenario == "not_found":
        raise ResourceNotFoundException("Feeder line 'FL-904' was not located in substation topology")
    elif scenario == "validation":
        raise ValidationFailedException(
            "Voltage phase angle out of bounds",
            details={"parameter": "phase_angle", "limit": "[-180, 180]", "received": 245.5}
        )
    elif scenario == "database":
        raise DatabaseUnavailableException("Unable to establish handshake with primary database replica")
    elif scenario == "config":
        raise ConfigurationException("Mandatory cryptographic certificate bundle path missing")
    else:
        # Simulate unexpected runtime error
        raise RuntimeError("Unexpected division by zero in downstream telemetry pipeline")
