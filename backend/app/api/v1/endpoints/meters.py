"""
Meter Lookup & Consumption Intelligence Endpoints.
Level 3: Core Electricity Intelligence.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.accounting.meter_service import MeterIntelligenceService
from app.core.exceptions import AppException
from app.core.responses import success_response
from app.database.models import HouseholdAggregateMeter
from app.database.session import get_db
from app.schemas.accounting import (
    MeterConsumptionProfileSchema,
    MeterLookupSchema,
)

router = APIRouter(prefix="/meters", tags=["Meter Intelligence"])


@router.get(
    "",
    summary="List All Demonstration Meters",
    description="Returns list of household aggregate meters with metadata and associated network assets."
)
async def list_all_meters(request: Request, db: Session = Depends(get_db)):
    meters = db.query(HouseholdAggregateMeter).all()
    results = []
    for m in meters:
        try:
            lookup = MeterIntelligenceService.lookup_meter(db, m.meter_code)
            results.append(lookup.__dict__)
        except Exception:
            results.append({
                "meter_id": m.id,
                "meter_code": m.meter_code,
                "household_count": m.household_count,
                "associated_asset_id": m.associated_asset_id,
                "is_simulated": m.is_simulated,
            })
    return success_response(data=results, request_id=request.headers.get("x-request-id"))


@router.get(
    "/{meter_code}",
    summary="Lookup Specific Meter by Identifier",
    description="Validates meter format, queries database, returns provenance, and rejects unknown identifiers."
)
async def get_meter(
    meter_code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        result = MeterIntelligenceService.lookup_meter(db, meter_code)
        return success_response(data=result.__dict__, request_id=request.headers.get("x-request-id"))
    except ValueError as val_err:
        raise AppException(
            code="ERR_INVALID_METER_FORMAT",
            message=str(val_err),
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"field": "meter_code"},
        )
    except KeyError as key_err:
        raise AppException(
            code="ERR_METER_NOT_FOUND",
            message=str(key_err),
            status_code=status.HTTP_404_NOT_FOUND,
            details={"field": "meter_code"},
        )


@router.get(
    "/{meter_code}/consumption",
    summary="Get Household Aggregate Consumption Profile",
    description="Returns aggregate intervals, peak power, missing readings, unusual changes, and data quality warnings."
)
async def get_meter_consumption(
    meter_code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        profile = MeterIntelligenceService.get_aggregate_consumption(db, meter_code)
        profile_dict = profile.__dict__.copy()
        profile_dict["data_quality_warnings"] = [f.__dict__ for f in profile.data_quality_warnings]
        profile_dict["trend_series"] = [t.__dict__ for t in profile.trend_series]

        return success_response(data=profile_dict, request_id=request.headers.get("x-request-id"))
    except ValueError as val_err:
        raise AppException(
            code="ERR_INVALID_METER_FORMAT",
            message=str(val_err),
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"field": "meter_code"},
        )
    except KeyError as key_err:
        raise AppException(
            code="ERR_METER_NOT_FOUND",
            message=str(key_err),
            status_code=status.HTTP_404_NOT_FOUND,
            details={"field": "meter_code"},
        )
