"""
Evidence Graph & What-If Analysis API Endpoints.
Level 5: Evidence Traceability and What-If Analysis.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.accounting.engine import EnergyAccountingEngine
from app.ai_services.hypothesis_engine import HypothesisGenerationEngine
from app.ai_services.prioritizer import InvestigationPrioritizer
from app.core.exceptions import AppException
from app.core.responses import success_response
from app.database.session import get_db
from app.investigation.graph_engine import EvidenceGraphBuilder
from app.investigation.what_if_engine import WhatIfCatalog, WhatIfSimulationEngine
from app.schemas.what_if import (
    BeforeAfterComparisonResponse,
    InvestigationGraphResponse,
    WhatIfCatalogItemSchema,
    WhatIfCorrectionRequest,
)

router = APIRouter(prefix="/investigation", tags=["Evidence Graph & What-If Analysis"])


@router.get(
    "/graph/{boundary_asset_code}",
    response_model=None,
    summary="Fetch Interactive Evidence Investigation Graph",
    description="Constructs an interactive Node-Link graph connecting Discrepancy -> Source Measurements -> Quality Findings -> Hypotheses -> Actions -> Outcome."
)
async def get_evidence_graph(
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

        graph_response = EvidenceGraphBuilder.build_graph(
            dossier=dossier,
            hypotheses=hypotheses,
            prioritization=prioritization,
        )

        return success_response(data=graph_response.model_dump(), request_id=request.headers.get("x-request-id"))

    except ValueError as val_err:
        raise AppException(
            code="ERR_BOUNDARY_NOT_FOUND",
            message=str(val_err),
            status_code=status.HTTP_404_NOT_FOUND,
            details={"field": "boundary_asset_code"},
        )
    except Exception as exc:
        raise AppException(
            code="ERR_GRAPH_GENERATION_FAILED",
            message=f"Failed to generate evidence investigation graph: {str(exc)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get(
    "/what-if/scenarios",
    response_model=None,
    summary="List Supported What-If Simulation Scenarios",
    description="Returns catalog of 5 repeatable what-if simulation templates with default parameters and impact descriptions."
)
async def list_what_if_scenarios(request: Request):
    catalog = WhatIfCatalog.list_catalog()
    catalog_data = [item.model_dump() for item in catalog]
    return success_response(data=catalog_data, request_id=request.headers.get("x-request-id"))


@router.post(
    "/what-if/simulate",
    response_model=None,
    summary="Execute What-If Simulation with Before/After Comparison",
    description="Runs in-memory hypothetical scenario without modifying production data, computing mathematical deltas and hypothesis shifts."
)
async def simulate_what_if(
    payload: WhatIfCorrectionRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        comparison_result = WhatIfSimulationEngine.run_simulation(
            db=db,
            request=payload,
        )

        return success_response(data=comparison_result.model_dump(), request_id=request.headers.get("x-request-id"))

    except ValueError as val_err:
        raise AppException(
            code="ERR_BOUNDARY_NOT_FOUND",
            message=str(val_err),
            status_code=status.HTTP_404_NOT_FOUND,
            details={"field": "boundary_asset_code"},
        )
    except Exception as exc:
        raise AppException(
            code="ERR_WHAT_IF_SIMULATION_FAILED",
            message=f"What-if simulation execution failed: {str(exc)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

