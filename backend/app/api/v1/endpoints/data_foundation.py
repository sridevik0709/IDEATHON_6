"""
Data Foundation Entity Query Endpoints.
Level 2: Data Foundation.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.database.session import get_db
from app.database.models import (
    AnomalyEvent,
    ConsumptionReading,
    DataQualityResult,
    DataSource,
    DistributionBoundaryReading,
    EvidenceRecord,
    HouseholdAggregateMeter,
    InvestigationCase,
    NetworkAsset,
    NetworkRelationship,
)
from app.data_processing.sources.registry import registry
from app.schemas.common import StandardSuccessResponse

router = APIRouter(tags=["Data Foundation Entities"])


@router.get(
    "/data-sources",
    summary="List All Registered Data Sources",
    description="Returns data source adapters (Synthetic, Local File, Utility Integration) with authorization status."
)
async def list_data_sources(request: Request, db: Session = Depends(get_db)):
    # Combine registered in-memory adapters with persisted DB entries
    db_sources = db.query(DataSource).all()
    if db_sources:
        sources_list = [
            {
                "id": s.id,
                "code": s.code,
                "name": s.name,
                "source_type": s.source_type,
                "is_active": s.is_active,
                "is_authorized": s.is_authorized,
                "configuration": s.configuration,
            }
            for s in db_sources
        ]
    else:
        sources_list = registry.list_adapters()

    return success_response(data=sources_list, request_id=request.headers.get("x-request-id"))


@router.get(
    "/network-assets",
    summary="List Network Assets & Topologies",
    description="Returns substations, feeders, and distribution transformers."
)
async def list_network_assets(
    request: Request,
    asset_type: Optional[str] = Query(None, description="Filter by SUBSTATION, FEEDER, or TRANSFORMER"),
    db: Session = Depends(get_db)
):
    query = db.query(NetworkAsset)
    if asset_type:
        query = query.filter(NetworkAsset.asset_type == asset_type.upper())
    assets = query.all()

    assets_data = [
        {
            "id": a.id,
            "asset_code": a.asset_code,
            "name": a.name,
            "asset_type": a.asset_type,
            "voltage_class": a.voltage_class,
            "rated_capacity_kva": a.rated_capacity_kva,
            "status": a.status,
            "location_coordinates": a.location_coordinates,
            "is_simulated": a.is_simulated,
        }
        for a in assets
    ]
    return success_response(data=assets_data, request_id=request.headers.get("x-request-id"))


@router.get(
    "/household-meters",
    summary="List Household Aggregate Meters",
    description="Returns consumer cluster aggregate meters without individual appliance or identity fabrication."
)
async def list_household_meters(request: Request, db: Session = Depends(get_db)):
    meters = db.query(HouseholdAggregateMeter).all()
    meters_data = [
        {
            "id": m.id,
            "meter_code": m.meter_code,
            "household_count": m.household_count,
            "associated_asset_id": m.associated_asset_id,
            "installation_type": m.installation_type,
            "phase_configuration": m.phase_configuration,
            "multiplier": m.multiplier,
            "is_simulated": m.is_simulated,
        }
        for m in meters
    ]
    return success_response(data=meters_data, request_id=request.headers.get("x-request-id"))


@router.get(
    "/anomalies",
    summary="List Grid Anomaly Events",
    description="Returns detected physical, telemetry, or topology anomalies."
)
async def list_anomalies(
    request: Request,
    severity: Optional[str] = Query(None, description="Filter by CRITICAL, HIGH, MEDIUM, LOW"),
    db: Session = Depends(get_db)
):
    query = db.query(AnomalyEvent)
    if severity:
        query = query.filter(AnomalyEvent.severity == severity.upper())
    anomalies = query.order_by(AnomalyEvent.detected_at.desc()).limit(50).all()

    anomalies_data = [
        {
            "id": a.id,
            "event_code": a.event_code,
            "anomaly_type": a.anomaly_type,
            "severity": a.severity,
            "related_asset_id": a.related_asset_id,
            "detected_at": a.detected_at.isoformat(),
            "discrepancy_kwh": a.discrepancy_kwh,
            "discrepancy_percent": a.discrepancy_percent,
            "status": a.status,
            "description": a.description,
            "is_simulated": a.is_simulated,
        }
        for a in anomalies
    ]
    return success_response(data=anomalies_data, request_id=request.headers.get("x-request-id"))


@router.get(
    "/investigation-cases",
    summary="List Forensic Investigation Cases",
    description="Returns investigation dockets with evidence records and outcomes."
)
async def list_investigation_cases(request: Request, db: Session = Depends(get_db)):
    cases = db.query(InvestigationCase).order_by(InvestigationCase.created_at.desc()).limit(20).all()
    cases_data = []

    for c in cases:
        evidence_list = [
            {
                "id": e.id,
                "evidence_type": e.evidence_type,
                "title": e.title,
                "hash_sha256": e.hash_sha256,
                "collected_by": e.collected_by,
                "collected_at": e.collected_at.isoformat(),
            }
            for e in c.evidence_records
        ]
        outcome_data = (
            {
                "outcome_type": c.outcome.outcome_type,
                "estimated_loss_kwh": c.outcome.estimated_loss_kwh,
                "estimated_financial_loss_inr": c.outcome.estimated_financial_loss_inr,
                "action_taken": c.outcome.action_taken,
            }
            if c.outcome
            else None
        )

        cases_data.append({
            "id": c.id,
            "case_number": c.case_number,
            "title": c.title,
            "priority": c.priority,
            "status": c.status,
            "summary": c.summary,
            "assigned_role": c.assigned_role,
            "evidence_count": len(evidence_list),
            "evidence": evidence_list,
            "outcome": outcome_data,
            "is_simulated": c.is_simulated,
            "created_at": c.created_at.isoformat(),
        })

    return success_response(data=cases_data, request_id=request.headers.get("x-request-id"))


@router.get(
    "/data-quality-audits",
    summary="List Data Quality Audit Findings",
    description="Returns data quality audit logs and error code diagnostics."
)
async def list_quality_audits(
    request: Request,
    passed: Optional[bool] = Query(None, description="Filter by passed (true/false)"),
    db: Session = Depends(get_db)
):
    query = db.query(DataQualityResult)
    if passed is not None:
        query = query.filter(DataQualityResult.passed == passed)
    results = query.order_by(DataQualityResult.evaluated_at.desc()).limit(50).all()

    results_data = [
        {
            "id": r.id,
            "target_type": r.target_type,
            "target_id": r.target_id,
            "quality_dimension": r.quality_dimension,
            "passed": r.passed,
            "score": r.score,
            "error_code": r.error_code,
            "diagnostic_message": r.diagnostic_message,
            "evaluated_at": r.evaluated_at.isoformat(),
        }
        for r in results
    ]
    return success_response(data=results_data, request_id=request.headers.get("x-request-id"))

