"""
Investigation & AI Assistant API Endpoints.
Level 4: AI-Assisted Investigation.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.accounting.engine import EnergyAccountingEngine
from app.ai_services.assistant import AiInvestigationAssistant
from app.ai_services.hypothesis_engine import HypothesisGenerationEngine
from app.ai_services.prioritizer import InvestigationPrioritizer
from app.core.exceptions import AppException
from app.core.responses import success_response
from app.database.session import get_db
from app.schemas.accounting import ReconciliationRequest
from app.schemas.investigation import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    EvidenceItemSchema,
    HypothesisAnalysisSchema,
    InvestigationDossierResponse,
    PrioritizationFactorSchema,
    PrioritizationReportSchema,
)

router = APIRouter(prefix="/investigation", tags=["AI Investigation & Forensics"])


def _serialize_dossier_response(
    dossier: Any,
    hypotheses: List[Any],
    prioritization: Any,
) -> Dict[str, Any]:
    """Helper to convert domain dataclasses into JSON-serializable dictionaries."""
    dossier_dict = dossier.__dict__.copy()
    dossier_dict["calculation_steps"] = [s.__dict__ for s in dossier.calculation_steps]
    dossier_dict["source_measurements"] = [s.__dict__ for s in dossier.source_measurements]
    dossier_dict["data_quality_findings"] = [f.__dict__ for f in dossier.data_quality_findings]

    hypotheses_serialized = []
    for h in hypotheses:
        h_dict = {
            "hypothesis_id": h.hypothesis_id,
            "code": h.code,
            "title": h.title,
            "category": h.category,
            "explanation": h.explanation,
            "plausibility": h.plausibility,
            "confidence_score": h.confidence_score,
            "confidence_rationale": h.confidence_rationale,
            "investigation_priority": h.investigation_priority,
            "investigation_status": h.investigation_status,
            "supporting_evidence": [ev.__dict__ for ev in h.supporting_evidence],
            "contradicting_evidence": [ev.__dict__ for ev in h.contradicting_evidence],
            "missing_evidence": h.missing_evidence,
            "additional_data_required": h.additional_data_required,
            "recommended_verification_steps": h.recommended_verification_steps,
        }
        hypotheses_serialized.append(h_dict)

    prioritization_dict = {
        "boundary_asset_code": prioritization.boundary_asset_code,
        "total_priority_score": prioritization.total_priority_score,
        "priority_level": prioritization.priority_level,
        "factors": [f.__dict__ for f in prioritization.factors],
        "top_recommended_hypothesis": prioritization.top_recommended_hypothesis,
        "operational_action_summary": prioritization.operational_action_summary,
    }

    return {
        "boundary_asset_code": dossier.boundary_asset_code,
        "boundary_asset_name": dossier.boundary_asset_name,
        "voltage_class": dossier.voltage_class,
        "analysis_period_start": str(dossier.time_window_start),
        "analysis_period_end": str(dossier.time_window_end),
        "accounting": dossier_dict,
        "hypotheses": hypotheses_serialized,
        "prioritization": prioritization_dict,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post(
    "/analyze",
    summary="Generate Multi-Hypothesis Investigation Dossier",
    description="Calculates energy reconciliation, evaluates all competing forensic hypotheses, and computes 6-factor explainable prioritization."
)
async def analyze_investigation(
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

        hypotheses = HypothesisGenerationEngine.analyze_discrepancy(dossier)
        prioritization = InvestigationPrioritizer.compute_priority(dossier, hypotheses)

        response_data = _serialize_dossier_response(dossier, hypotheses, prioritization)
        return success_response(data=response_data, request_id=request.headers.get("x-request-id"))

    except ValueError as val_err:
        raise AppException(
            code="ERR_BOUNDARY_NOT_FOUND",
            message=str(val_err),
            status_code=status.HTTP_404_NOT_FOUND,
            details={"field": "boundary_asset_code"},
        )
    except Exception as exc:
        raise AppException(
            code="ERR_INVESTIGATION_ANALYSIS_FAILED",
            message=f"Failed to generate investigation dossier: {str(exc)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get(
    "/dossier/{boundary_asset_code}",
    summary="Fetch Investigation Dossier for Boundary Asset",
    description="Convenience GET endpoint to retrieve the latest multi-hypothesis dossier and explainable priority score."
)
async def get_investigation_dossier(
    boundary_asset_code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        dossier = EnergyAccountingEngine.reconcile_boundary(
            db=db,
            boundary_asset_code=boundary_asset_code,
        )

        hypotheses = HypothesisGenerationEngine.analyze_discrepancy(dossier)
        prioritization = InvestigationPrioritizer.compute_priority(dossier, hypotheses)

        response_data = _serialize_dossier_response(dossier, hypotheses, prioritization)
        return success_response(data=response_data, request_id=request.headers.get("x-request-id"))

    except ValueError as val_err:
        raise AppException(
            code="ERR_BOUNDARY_NOT_FOUND",
            message=str(val_err),
            status_code=status.HTTP_404_NOT_FOUND,
            details={"boundary_asset_code": boundary_asset_code},
        )
    except Exception as exc:
        raise AppException(
            code="ERR_INVESTIGATION_ANALYSIS_FAILED",
            message=f"Failed to fetch investigation dossier: {str(exc)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post(
    "/assistant",
    summary="AI Investigation Assistant Forensic Q&A",
    description="Interactive Q&A assistant. Answers queries with evidence citations and guardrail validations, operating with automatic deterministic fallback if no external API key is set."
)
async def query_ai_assistant(
    payload: AssistantQueryRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        dossier = EnergyAccountingEngine.reconcile_boundary(
            db=db,
            boundary_asset_code=payload.boundary_asset_code,
            start_time=payload.start_time,
            end_time=payload.end_time,
        )

        hypotheses = HypothesisGenerationEngine.analyze_discrepancy(dossier)
        prioritization = InvestigationPrioritizer.compute_priority(dossier, hypotheses)

        assistant_resp: AssistantQueryResponse = await AiInvestigationAssistant.process_query(
            query=payload.query,
            dossier=dossier,
            hypotheses=hypotheses,
            prioritization=prioritization,
        )

        return success_response(data=assistant_resp.model_dump(), request_id=request.headers.get("x-request-id"))

    except ValueError as val_err:
        raise AppException(
            code="ERR_BOUNDARY_NOT_FOUND",
            message=str(val_err),
            status_code=status.HTTP_404_NOT_FOUND,
            details={"field": "boundary_asset_code"},
        )
    except Exception as exc:
        raise AppException(
            code="ERR_ASSISTANT_QUERY_FAILED",
            message=f"AI Investigation Assistant query failed: {str(exc)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

