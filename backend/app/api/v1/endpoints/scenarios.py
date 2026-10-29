"""
Scenario Demonstration and Execution Endpoints.
Level 2: Data Foundation.
"""

from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundException, ValidationFailedException
from app.core.responses import success_response
from app.database.session import get_db
from app.database.models import ScenarioRun
from app.data_processing.synthetic_generator import (
    SyntheticGridGenerator,
    save_scenario_to_database,
)
from app.schemas.common import StandardSuccessResponse
from app.schemas.data_foundation import (
    ScenarioDescriptor,
    ScenarioExecutionRequest,
    ScenarioExecutionResponse,
)

router = APIRouter(prefix="/scenarios", tags=["Demonstration Scenarios"])

SCENARIO_REGISTRY = {
    "SCENARIO_A": {
        "scenario_code": "SCENARIO_A",
        "scenario_name": "Scenario A: Normal Operation",
        "description": "Standard physics balance across Substation -> Feeders -> DTs -> Aggregate Meters with normal technical line losses.",
        "documented_inputs": {
            "load_profile": "Standard diurnal dual-peak load curve (morning and evening)",
            "technical_loss_model": "I^2 R resistance model (approx. 2.8% on distribution transformers)",
            "observation_window": "24 hours (1-hour intervals)",
            "telemetry_health": "100% complete, uncorrupted, on-time packets",
        },
        "expected_outcomes": {
            "substation_feeder_balance": "Balanced within technical loss bounds (2.5% - 3.2%)",
            "unaccounted_energy": "0.0 kWh (zero non-technical loss)",
            "data_quality_pass_rate": "100%",
            "anomaly_events_generated": 0,
            "status": "BALANCED_NORMAL",
        },
    },
    "SCENARIO_B": {
        "scenario_code": "SCENARIO_B",
        "scenario_name": "Scenario B: Delayed Downstream Readings",
        "description": "Downstream aggregate meter packets from DT-102 cluster arrive delayed due to telecommunication lag, creating a temporary apparent deficit.",
        "documented_inputs": {
            "delayed_assets": ["AGG-MTR-DT102-A", "AGG-MTR-DT102-B"],
            "delayed_hours_window": "14:00 to 18:00 UTC",
            "missing_packet_count": 10,
            "boundary_status": "DT-102 primary input meter reports continuous normal energy flow",
        },
        "expected_outcomes": {
            "apparent_loss_gap": "54.2% temporary deficit on DT-102 during missing window",
            "data_quality_flags": "ERR_MISSING_READING / DELAYED_PENDING_INGEST",
            "anomaly_event": "DELAYED_READING_ACCUMULATION (Severity: MEDIUM)",
            "reconciliation": "No false theft accusations; backfilled batch resolves gap",
            "status": "DELAYED_TELEMETRY_DETECTED",
        },
    },
    "SCENARIO_C": {
        "scenario_code": "SCENARIO_C",
        "scenario_name": "Scenario C: Incorrect Downstream Asset Mapping",
        "description": "Meter AGG-MTR-DT101-B physically fed from DT-101 is erroneously linked to DT-102 in GIS/database topology.",
        "documented_inputs": {
            "mismapped_meter": "AGG-MTR-DT101-B",
            "physical_source": "DT-11KV-415V-101",
            "erroneous_gis_parent": "DT-11KV-415V-102",
        },
        "expected_outcomes": {
            "dt_101_impact": "Apparent severe energy loss (~38% deficit)",
            "dt_102_impact": "Negative technical loss (-26.4% apparent surplus / physics violation)",
            "anomaly_event": "TOPOLOGY_MAPPING_ERROR (Severity: HIGH)",
            "corrective_action": "Topology reconciliation recommended: GIS reassignment",
            "status": "TOPOLOGY_MISMATCH_DETECTED",
        },
    },
    "SCENARIO_D": {
        "scenario_code": "SCENARIO_D",
        "scenario_name": "Scenario D: Residual Accounting Discrepancy",
        "description": "Statistically persistent commercial electricity theft via direct busbar tap on DT-103 during night hours.",
        "documented_inputs": {
            "target_asset": "DT-11KV-415V-103 (Sector 6 Commercial Market)",
            "theft_window": "18:00 to 04:00 daily",
            "bypass_rate": "42% load bypassed past aggregate consumer meters",
            "meter_health": "Meters are functional; discrepancy represents true physical unmetered load",
        },
        "expected_outcomes": {
            "unaccounted_loss": "21.8% residual non-technical loss (exceeds 3% technical threshold)",
            "anomaly_event": "RESIDUAL_ENERGY_DISCREPANCY (Severity: CRITICAL)",
            "investigation_case": "Automated creation of CASE-2026-DT103-THEFT-001",
            "evidence_record": "Cryptographically hashed balance snapshot (SHA-256)",
            "investigation_outcome": "Estimated financial loss calculated in INR; field dispatch triggered",
            "status": "THEFT_ANOMALY_CONFIRMED",
        },
    },
    "SCENARIO_E": {
        "scenario_code": "SCENARIO_E",
        "scenario_name": "Scenario E: Multiple Simultaneous Data-Quality Problems",
        "description": "Composite sensor malfunctions: negative energy, voltage surge, future timestamp, and duplicate packets.",
        "documented_inputs": {
            "negative_reading": "Reversed CT polarity (-42.5 kWh)",
            "voltage_surge": "Overvoltage spike (495V on 230V LV terminal)",
            "timestamp_skew": "Corrupted clock pointing to +365 days in future",
            "duplicate_packets": "Conflicting dual intervals submitted for same timestamp",
        },
        "expected_outcomes": {
            "data_quality_pass_rate": "Drops to 78% (below 95% acceptance threshold)",
            "rejected_records": "Corrupted readings excluded from balance calculations",
            "anomaly_event": "DATA_QUALITY_DEGRADATION (Severity: HIGH)",
            "status": "DATA_QUALITY_REJECTED",
        },
    },
}


@router.get(
    "",
    response_model=StandardSuccessResponse[List[ScenarioDescriptor]],
    summary="List 5 Repeatable Demonstration Scenarios",
    description="Returns full catalog of the 5 reproducible scenarios with documented inputs and expected outcomes."
)
async def list_scenarios(request: Request) -> StandardSuccessResponse[List[ScenarioDescriptor]]:
    scenarios_list = [
        ScenarioDescriptor(
            scenario_code=v["scenario_code"],
            scenario_name=v["scenario_name"],
            description=v["description"],
            documented_inputs=v["documented_inputs"],
            expected_outcomes=v["expected_outcomes"],
        )
        for v in SCENARIO_REGISTRY.values()
    ]
    return success_response(data=scenarios_list, request_id=request.headers.get("x-request-id"))


@router.post(
    "/run",
    response_model=StandardSuccessResponse[ScenarioExecutionResponse],
    summary="Execute Repeatable Demonstration Scenario",
    description="Generates deterministic synthetic grid telemetry for Scenario A, B, C, D, or E and persists to database."
)
async def run_scenario(
    payload: ScenarioExecutionRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> StandardSuccessResponse[ScenarioExecutionResponse]:
    code = payload.scenario_code.upper().strip()
    if code not in SCENARIO_REGISTRY:
        raise ValidationFailedException(
            f"Scenario '{code}' is unrecognized. Valid scenarios: {list(SCENARIO_REGISTRY.keys())}",
            details={"allowed": list(SCENARIO_REGISTRY.keys()), "received": code}
        )

    generator = SyntheticGridGenerator(seed=payload.seed)
    
    if code == "SCENARIO_A":
        scenario_data = generator.generate_scenario_a_normal(hours=24)
    elif code == "SCENARIO_B":
        scenario_data = generator.generate_scenario_b_delayed(hours=24)
    elif code == "SCENARIO_C":
        scenario_data = generator.generate_scenario_c_mapping_error(hours=24)
    elif code == "SCENARIO_D":
        scenario_data = generator.generate_scenario_d_theft_discrepancy(hours=24)
    elif code == "SCENARIO_E":
        scenario_data = generator.generate_scenario_e_data_quality_failures(hours=24)
    else:
        raise HTTPException(status_code=400, detail="Unhandled scenario execution")

    run_id = None
    if payload.persist_to_database:
        run_record = save_scenario_to_database(db, scenario_data)
        run_id = run_record.id

    response_data = ScenarioExecutionResponse(
        scenario_code=scenario_data["scenario_code"],
        scenario_name=scenario_data["scenario_name"],
        seed=payload.seed,
        status="COMPLETED",
        records_generated_count=len(scenario_data["boundary_readings"]) + len(scenario_data["consumption_readings"]),
        summary_metrics=scenario_data["metrics"],
        anomaly_count=len(scenario_data.get("anomalies", [])),
        cases_generated_count=len(scenario_data.get("cases", [])),
        run_id=run_id,
        executed_at=datetime.now(timezone.utc),
    )

    return success_response(data=response_data, request_id=request.headers.get("x-request-id"))


@router.get(
    "/history",
    summary="List Historical Scenario Runs",
    description="Returns audit history of past scenario executions."
)
async def get_scenario_history(
    request: Request,
    db: Session = Depends(get_db)
):
    runs = db.query(ScenarioRun).order_by(ScenarioRun.started_at.desc()).limit(20).all()
    history = [
        {
            "id": r.id,
            "scenario_code": r.scenario_code,
            "scenario_name": r.scenario_name,
            "seed": r.seed,
            "status": r.status,
            "records_count": r.records_generated_count,
            "metrics": r.summary_metrics,
            "started_at": r.started_at.isoformat(),
        }
        for r in runs
    ]
    return success_response(data=history, request_id=request.headers.get("x-request-id"))

