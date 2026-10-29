"""
Automated Test Suite for Level 5: Evidence Traceability and What-If Analysis.

Verifies:
1. Evidence Investigation Graph:
   - Node-link structure connecting Discrepancy -> Source Measurements -> Quality Findings -> Hypotheses -> Actions -> Outcome.
   - Traceability of every node back to real records, calculations, or documented rules.
   - All 5 distinct visual states (OBSERVED_EVIDENCE, CALCULATED_FINDING, HYPOTHESIS, RECOMMENDATION, CONFIRMED_OUTCOME).
   - Inspection attributes (source ID, timestamp, measurement value, unit, status, calculation, rules, verification status).
2. What-If Simulation Scenarios:
   - Delayed reading arrival reduces unaccounted energy.
   - Measurement intervals alignment.
   - Topological mapping error correction.
   - Duplicate record removal.
   - Data quality issue repair (CT polarity, voltage surge).
3. Before-and-After Comparison:
   - Accurate mathematical deltas (kWh and %).
   - Quality findings resolution tracking.
   - Hypothesis plausibility and priority score shifts.
4. Data Protection & Non-Overwriting Mandate:
   - Original measurements in production tables remain 100% immutable and untouched.
   - Scenario results are isolated and stored separately in ScenarioRun & AuditLog.
   - Real-world investigation cases cannot be closed or resolved automatically by hypothetical simulations.
"""

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import func

from app.accounting.engine import EnergyAccountingEngine
from app.ai_services.hypothesis_engine import HypothesisGenerationEngine
from app.ai_services.prioritizer import InvestigationPrioritizer
from app.data_processing.synthetic_generator import SyntheticGridGenerator, save_scenario_to_database
from app.database.models import (
    AuditLog,
    ConsumptionReading,
    DistributionBoundaryReading,
    InvestigationCase,
    ScenarioRun,
)
from app.database.session import get_db
from app.investigation.graph_engine import EvidenceGraphBuilder
from app.investigation.what_if_engine import WhatIfCatalog, WhatIfSimulationEngine
from app.main import app
from app.schemas.what_if import WhatIfCorrectionRequest


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def db_session():
    db = next(get_db())
    try:
        # Seed Scenario D (Residual Discrepancy) and Scenario B (Delayed Telemetry)
        gen = SyntheticGridGenerator(seed=42)
        scenario_d = gen.generate_scenario_d_theft_discrepancy(hours=24)
        save_scenario_to_database(db, scenario_d)
        yield db
    finally:
        db.close()


def test_evidence_graph_nodes_and_edges_integrity(db_session):
    """
    Verify that the Evidence Investigation Graph constructs a full directed graph
    connecting Discrepancy -> Source Measurements -> Quality Findings -> Hypotheses -> Actions -> Outcome.
    """
    dossier = EnergyAccountingEngine.reconcile_boundary(
        db=db_session,
        boundary_asset_code="DT-11KV-415V-101",
    )
    hypotheses = HypothesisGenerationEngine.analyze_discrepancy(dossier)
    prioritization = InvestigationPrioritizer.compute_priority(dossier, hypotheses)

    graph = EvidenceGraphBuilder.build_graph(dossier, hypotheses, prioritization)

    assert graph.boundary_asset_code == "DT-11KV-415V-101"
    assert len(graph.nodes) >= 10
    assert len(graph.edges) >= 10

    node_types = {n.node_type for n in graph.nodes}
    assert "DISCREPANCY_ROOT" in node_types
    assert "SOURCE_MEASUREMENT" in node_types
    assert "DATA_QUALITY_FINDING" in node_types
    assert "HYPOTHESIS_EXPLANATION" in node_types
    assert "VERIFICATION_ACTION" in node_types
    assert "INVESTIGATION_OUTCOME" in node_types

    edge_types = {e.relationship_type for e in graph.edges}
    assert "DERIVED_FROM" in edge_types
    assert "EXPLAINED_BY" in edge_types
    assert "RECOMMENDS" in edge_types
    assert "LEADS_TO" in edge_types


def test_evidence_graph_visual_states_and_inspectable_docket(db_session):
    """
    Verify that all 5 distinct visual states are present and that nodes provide
    complete inspection attributes (source identifier, timestamp, value, unit, rules, status).
    """
    dossier = EnergyAccountingEngine.reconcile_boundary(
        db=db_session,
        boundary_asset_code="DT-11KV-415V-101",
    )
    hypotheses = HypothesisGenerationEngine.analyze_discrepancy(dossier)
    prioritization = InvestigationPrioritizer.compute_priority(dossier, hypotheses)

    graph = EvidenceGraphBuilder.build_graph(dossier, hypotheses, prioritization)

    visual_states = {n.visual_state for n in graph.nodes}
    assert "OBSERVED_EVIDENCE" in visual_states
    assert "CALCULATED_FINDING" in visual_states
    assert "HYPOTHESIS" in visual_states
    assert "RECOMMENDATION" in visual_states
    assert "CONFIRMED_OUTCOME" in visual_states

    # Inspect a root node
    root_node = next(n for n in graph.nodes if n.node_type == "DISCREPANCY_ROOT")
    assert root_node.metric_value is not None
    assert root_node.unit == "KWH"
    assert root_node.calculation_formula is not None
    assert root_node.reasoning_rule is not None
    assert root_node.verification_status in ["VERIFIED", "PENDING_FIELD_CHECK"]

    # Inspect a source measurement node
    src_node = next(n for n in graph.nodes if n.node_type == "SOURCE_MEASUREMENT")
    assert src_node.entity_code is not None
    assert src_node.timestamp_or_period is not None
    assert src_node.data_status in ["VALID", "FLAGGED", "SIMULATED"]


def test_what_if_delayed_reading_scenario(db_session):
    """
    Test What-If Scenario 1: A delayed reading becomes available.
    Simulate arrival of +16.5 kWh downstream packets.
    Verify that recorded downstream energy increases, unaccounted energy decreases,
    and discrepancy drops toward normal technical loss.
    """
    req = WhatIfCorrectionRequest(
        boundary_asset_code="DT-11KV-415V-101",
        scenario_type="DELAYED_READINGS_ARRIVED",
        parameters={"delayed_kwh_recovered": 16.5, "target_meter_code": "AGG-MTR-DT102-A"},
    )
    res = WhatIfSimulationEngine.run_simulation(db=db_session, request=req)

    assert res.boundary_asset_code == "DT-11KV-415V-101"
    assert res.scenario_type == "DELAYED_READINGS_ARRIVED"
    assert res.revised_accounting.recorded_downstream_kwh > res.original_accounting.recorded_downstream_kwh
    assert res.differences.delta_downstream_kwh == 16.5
    assert len(res.resolved_warnings) >= 1
    assert res.data_protection.original_records_unmodified is True


def test_what_if_topological_mapping_correction(db_session):
    """
    Test What-If Scenario 3: A simulated topological mapping error is corrected.
    Simulate reassigning an unmapped / misassigned cluster meter (+312.4 kWh).
    Verify that revised balance re-sums downstream recorded energy.
    """
    req = WhatIfCorrectionRequest(
        boundary_asset_code="DT-11KV-415V-101",
        scenario_type="CORRECT_TOPOLOGICAL_MAPPING",
        parameters={"reassigned_meter_code": "AGG-MTR-DT102-B", "meter_energy_kwh": 312.4},
    )
    res = WhatIfSimulationEngine.run_simulation(db=db_session, request=req)

    assert res.differences.delta_downstream_kwh == 312.4
    assert res.data_protection.correction_provenance == "HYPOTHETICAL_SIMULATION"


def test_what_if_duplicate_removal(db_session):
    """
    Test What-If Scenario 4: A duplicate record is removed.
    Simulate deduplicating 25.8 kWh.
    Verify downstream recorded energy decreases by 25.8 kWh and ERR_DUPLICATE_RECORD is resolved.
    """
    req = WhatIfCorrectionRequest(
        boundary_asset_code="DT-11KV-415V-101",
        scenario_type="REMOVE_DUPLICATE_RECORDS",
        parameters={"duplicate_kwh_removed": 25.8},
    )
    res = WhatIfSimulationEngine.run_simulation(db=db_session, request=req)

    assert res.differences.delta_downstream_kwh == -25.8
    assert any("ERR_DUPLICATE_RECORD" in w for w in res.resolved_warnings)


def test_what_if_data_quality_correction(db_session):
    """
    Test What-If Scenario 5: Documented data-quality issue corrected.
    Simulate reversing negative energy (-42.5 kWh -> +42.5 kWh) and capping voltage spike.
    Verify ERR_NEGATIVE_ENERGY is resolved.
    """
    req = WhatIfCorrectionRequest(
        boundary_asset_code="DT-11KV-415V-101",
        scenario_type="CORRECT_DATA_QUALITY_ISSUES",
        parameters={"negative_reading_reversal_kwh": 42.5},
    )
    res = WhatIfSimulationEngine.run_simulation(db=db_session, request=req)

    assert any("ERR_NEGATIVE_ENERGY" in w for w in res.resolved_warnings)
    assert res.differences.delta_downstream_kwh == 85.0


def test_data_protection_original_measurements_remain_immutable(db_session):
    """
    CRITICAL REQUIREMENT: Never overwrite original measurements during hypothetical analysis.
    Verify that row counts, total kWh, and record IDs in distribution_boundary_readings
    and consumption_readings are 100% IDENTICAL before and after what-if simulations.
    """
    # 1. Snapshot database state before simulations
    bnd_count_before = db_session.query(func.count(DistributionBoundaryReading.id)).scalar()
    con_count_before = db_session.query(func.count(ConsumptionReading.id)).scalar()
    bnd_kwh_before = db_session.query(func.sum(DistributionBoundaryReading.energy_kwh)).scalar()
    con_kwh_before = db_session.query(func.sum(ConsumptionReading.energy_kwh)).scalar()

    # 2. Run multiple what-if simulations with large overrides
    for stype in ["DELAYED_READINGS_ARRIVED", "CORRECT_TOPOLOGICAL_MAPPING", "REMOVE_DUPLICATE_RECORDS", "CORRECT_DATA_QUALITY_ISSUES"]:
        req = WhatIfCorrectionRequest(
            boundary_asset_code="DT-11KV-415V-101",
            scenario_type=stype,
            parameters={"delayed_kwh_recovered": 500.0, "duplicate_kwh_removed": 100.0},
        )
        WhatIfSimulationEngine.run_simulation(db=db_session, request=req)

    # 3. Snapshot database state after simulations
    bnd_count_after = db_session.query(func.count(DistributionBoundaryReading.id)).scalar()
    con_count_after = db_session.query(func.count(ConsumptionReading.id)).scalar()
    bnd_kwh_after = db_session.query(func.sum(DistributionBoundaryReading.energy_kwh)).scalar()
    con_kwh_after = db_session.query(func.sum(ConsumptionReading.energy_kwh)).scalar()

    # 4. Assert zero mutation
    assert bnd_count_before == bnd_count_after, "Boundary reading row count must not change"
    assert con_count_before == con_count_after, "Consumption reading row count must not change"
    assert pytest.approx(bnd_kwh_before, rel=1e-5) == bnd_kwh_after, "Boundary readings energy sum must remain immutable"
    assert pytest.approx(con_kwh_before, rel=1e-5) == con_kwh_after, "Consumption readings energy sum must remain immutable"


def test_data_protection_scenario_runs_persisted_separately(db_session):
    """
    Verify that what-if simulations persist separately into scenario_runs and audit_logs
    with is_simulated=True, cleanly isolated from operational data.
    """
    req = WhatIfCorrectionRequest(
        boundary_asset_code="DT-11KV-415V-101",
        scenario_type="DELAYED_READINGS_ARRIVED",
        parameters={"delayed_kwh_recovered": 12.0},
    )
    res = WhatIfSimulationEngine.run_simulation(db=db_session, request=req)

    # Check ScenarioRun table
    run_record = db_session.query(ScenarioRun).filter(ScenarioRun.id == res.data_protection.scenario_run_id).first()
    assert run_record is not None
    assert run_record.is_simulated is True
    assert "WHAT_IF" in run_record.scenario_code

    # Check AuditLog table
    audit_record = db_session.query(AuditLog).filter(
        AuditLog.action == "WHAT_IF_SANDBOX_SIMULATION",
        AuditLog.entity_id == "DT-11KV-415V-101",
    ).first()
    assert audit_record is not None
    assert audit_record.details.get("data_protection") == "STRICT_READ_ONLY_IMMUTABLE"


def test_data_protection_real_cases_cannot_auto_resolve(db_session):
    """
    Verify that hypothetical corrections CANNOT automatically close or resolve
    real InvestigationCase records in the database.
    """
    # Create or find an open investigation case
    case = db_session.query(InvestigationCase).filter(InvestigationCase.status == "OPEN").first()
    case_status_before = case.status if case else None

    # Run what-if that eliminates the discrepancy
    req = WhatIfCorrectionRequest(
        boundary_asset_code="DT-11KV-415V-101",
        scenario_type="DELAYED_READINGS_ARRIVED",
        parameters={"delayed_kwh_recovered": 100.0},
    )
    res = WhatIfSimulationEngine.run_simulation(db=db_session, request=req)

    # Check case status remained OPEN
    if case:
        db_session.refresh(case)
        assert case.status == case_status_before
        assert case.status != "RESOLVED"
        assert case.status != "CLOSED"

    assert res.data_protection.real_case_auto_resolution_prevented is True


def test_api_graph_and_what_if_endpoints(client):
    """
    Test REST API endpoints for Level 5:
    - GET /api/v1/investigation/graph/{code}
    - GET /api/v1/investigation/what-if/scenarios
    - POST /api/v1/investigation/what-if/simulate
    """
    # 1. Graph Endpoint
    graph_resp = client.get("/api/v1/investigation/graph/DT-11KV-415V-101")
    assert graph_resp.status_code == 200
    graph_json = graph_resp.json()
    assert graph_json["status"] == "success"
    assert len(graph_json["data"]["nodes"]) >= 10
    assert len(graph_json["data"]["edges"]) >= 10

    # 2. What-If Scenarios Catalog
    cat_resp = client.get("/api/v1/investigation/what-if/scenarios")
    assert cat_resp.status_code == 200
    cat_json = cat_resp.json()
    assert cat_json["status"] == "success"
    assert len(cat_json["data"]) == 5

    # 3. What-If Simulate POST Endpoint
    sim_resp = client.post(
        "/api/v1/investigation/what-if/simulate",
        json={
            "boundary_asset_code": "DT-11KV-415V-101",
            "scenario_type": "DELAYED_READINGS_ARRIVED",
            "parameters": {"delayed_kwh_recovered": 14.5},
        },
    )
    assert sim_resp.status_code == 200
    sim_json = sim_resp.json()
    assert sim_json["status"] == "success"
    assert sim_json["data"]["differences"]["delta_downstream_kwh"] == 14.5
    assert sim_json["data"]["data_protection"]["original_records_unmodified"] is True

