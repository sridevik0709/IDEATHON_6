"""
Energy Accounting & Discrepancy Explorer Endpoints.
Level 3: Core Electricity Intelligence.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.accounting.engine import EnergyAccountingEngine
from app.accounting.data_quality import DataQualityEngine
from app.core.exceptions import AppException
from app.core.responses import success_response
from app.database.models import (
    HouseholdAggregateMeter,
    NetworkAsset,
    NetworkRelationship,
)
from app.database.session import get_db
from app.schemas.accounting import (
    AccountingBoundaryItemSchema,
    ReconciliationRequest,
    ReconciliationResponse,
)

router = APIRouter(prefix="/accounting", tags=["Energy Accounting & Discrepancy Engine"])


@router.get(
    "/boundaries",
    summary="List Supported Network Accounting Boundaries",
    description="Returns available physical distribution boundaries (Substations, Feeders, Distribution Transformers)."
)
async def list_accounting_boundaries(request: Request, db: Session = Depends(get_db)):
    assets = db.query(NetworkAsset).filter(
        NetworkAsset.asset_type.in_(["SUBSTATION", "FEEDER", "TRANSFORMER"])
    ).all()

    boundaries = []
    for a in assets:
        if a.asset_type == "TRANSFORMER":
            child_count = db.query(HouseholdAggregateMeter).filter(
                HouseholdAggregateMeter.associated_asset_id == a.id
            ).count()
            child_type = "HOUSEHOLD_AGGREGATE_METERS"
        elif a.asset_type == "FEEDER":
            child_count = db.query(NetworkRelationship).filter(
                NetworkRelationship.parent_asset_id == a.id,
                NetworkRelationship.is_current == True,
            ).count()
            child_type = "DISTRIBUTION_TRANSFORMERS"
        elif a.asset_type == "SUBSTATION":
            child_count = db.query(NetworkRelationship).filter(
                NetworkRelationship.parent_asset_id == a.id,
                NetworkRelationship.is_current == True,
            ).count()
            child_type = "FEEDERS"
        else:
            child_count = 0
            child_type = "UNKNOWN"

        boundaries.append({
            "asset_code": a.asset_code,
            "name": a.name,
            "asset_type": a.asset_type,
            "voltage_class": a.voltage_class,
            "rated_capacity_kva": a.rated_capacity_kva,
            "child_entities_count": child_count,
            "child_type": child_type,
            "status": a.status,
        })

    return success_response(data=boundaries, request_id=request.headers.get("x-request-id"))


@router.post(
    "/reconcile",
    summary="Reconcile Distribution Boundary Energy Balance",
    description="Executes deterministic energy accounting calculation with inspectable steps, source traces, and neutral classification."
)
async def reconcile_boundary(
    payload: ReconciliationRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        dossier = EnergyAccountingEngine.reconcile_boundary(
            db=db,
            boundary_asset_code=payload.boundary_asset_code,
            start_time=payload.start_time,
            end_time=payload.end_time,
            custom_technical_loss_pct=payload.custom_technical_loss_pct,
        )

        dossier_dict = dossier.__dict__.copy()
        dossier_dict["calculation_steps"] = [s.__dict__ for s in dossier.calculation_steps]
        dossier_dict["source_measurements"] = [s.__dict__ for s in dossier.source_measurements]
        dossier_dict["data_quality_findings"] = [f.__dict__ for f in dossier.data_quality_findings]

        return success_response(data=dossier_dict, request_id=request.headers.get("x-request-id"))
    except ValueError as val_err:
        raise AppException(
            code="ERR_BOUNDARY_NOT_FOUND",
            message=str(val_err),
            status_code=status.HTTP_404_NOT_FOUND,
            details={"field": "boundary_asset_code"},
        )
    except Exception as exc:
        raise AppException(
            code="ERR_ACCOUNTING_CALCULATION_FAILED",
            message=f"Energy accounting calculation failed: {str(exc)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
