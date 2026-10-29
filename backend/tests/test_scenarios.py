"""
Tests for the 5 Repeatable Demonstration Scenarios.
Verifies Scenario A, B, C, D, and E inputs, outputs, anomalies, and DB persistence.
"""

from sqlalchemy.orm import Session
from app.database.session import get_engine, init_database
from app.database.models import AnomalyEvent, InvestigationCase, ScenarioRun
from app.data_processing.synthetic_generator import (
    SyntheticGridGenerator,
    save_scenario_to_database,
)


def test_scenario_a_normal_operation():
    """Verify Scenario A produces balanced physics and zero anomalies."""
    gen = SyntheticGridGenerator(seed=42)
    res = gen.generate_scenario_a_normal(hours=24)

    assert res["scenario_code"] == "SCENARIO_A"
    assert len(res["anomalies"]) == 0
    assert res["metrics"]["status"] == "BALANCED_NORMAL"
    assert 2.0 <= res["metrics"]["technical_loss_percent"] <= 4.0
    assert res["metrics"]["unaccounted_residual_percent"] == 0.0


def test_scenario_b_delayed_readings():
    """Verify Scenario B flags delayed interval packets and generates anomaly."""
    gen = SyntheticGridGenerator(seed=42)
    res = gen.generate_scenario_b_delayed(hours=24)

    assert res["scenario_code"] == "SCENARIO_B"
    assert len(res["anomalies"]) == 1
    anom = res["anomalies"][0]
    assert anom["anomaly_type"] == "DELAYED_READING_ACCUMULATION"
    assert anom["severity"] == "MEDIUM"

    # Verify delayed validation status on target meter readings
    delayed_count = sum(1 for r in res["consumption_readings"] if r["validation_status"] == "DELAYED")
    assert delayed_count == 10


def test_scenario_c_mapping_error():
    """Verify Scenario C identifies negative loss / topology mismatch."""
    gen = SyntheticGridGenerator(seed=42)
    res = gen.generate_scenario_c_mapping_error(hours=24)

    assert res["scenario_code"] == "SCENARIO_C"
    assert len(res["anomalies"]) == 1
    anom = res["anomalies"][0]
    assert anom["anomaly_type"] == "TOPOLOGY_MAPPING_ERROR"
    assert anom["severity"] == "HIGH"
    assert anom["discrepancy_percent"] < 0  # Negative loss indication


def test_scenario_d_theft_discrepancy_and_case():
    """Verify Scenario D detects residual accounting gap and auto-generates investigation case docket."""
    gen = SyntheticGridGenerator(seed=42)
    res = gen.generate_scenario_d_theft_discrepancy(hours=24)

    assert res["scenario_code"] == "SCENARIO_D"
    assert len(res["anomalies"]) == 1
    anom = res["anomalies"][0]
    assert anom["anomaly_type"] == "RESIDUAL_ENERGY_DISCREPANCY"
    assert anom["severity"] == "CRITICAL"
    assert anom["discrepancy_percent"] > 15.0

    # Verify Investigation Case Docket
    assert len(res["cases"]) == 1
    case = res["cases"][0]
    assert "CASE-" in case["case_number"]
    assert len(case["evidence"]) >= 1
    # Evidence must have valid SHA-256 hash
    assert len(case["evidence"][0]["hash_sha256"]) == 64
    assert case["outcome"]["outcome_type"] == "CONFIRMED_NON_TECHNICAL_LOSS"
    assert case["outcome"]["estimated_financial_loss_inr"] > 0


def test_scenario_e_data_quality_failures():
    """Verify Scenario E injects and flags multi-dimensional data quality anomalies."""
    gen = SyntheticGridGenerator(seed=42)
    res = gen.generate_scenario_e_data_quality_failures(hours=24)

    assert res["scenario_code"] == "SCENARIO_E"
    assert len(res["anomalies"]) == 1
    assert res["anomalies"][0]["anomaly_type"] == "DATA_QUALITY_DEGRADATION"

    # Find injected negative reading
    has_negative = any(r["energy_kwh"] < 0 for r in res["consumption_readings"])
    assert has_negative is True

    # Find injected overvoltage
    has_spike = any(r.get("voltage_v", 0) > 400.0 for r in res["boundary_readings"])
    assert has_spike is True


def test_scenario_database_persistence():
    """Verify end-to-end database persistence of scenario run docket and records."""
    init_database()
    engine = get_engine()
    db = Session(bind=engine)
    try:
        gen = SyntheticGridGenerator(seed=77)
        scenario_d = gen.generate_scenario_d_theft_discrepancy(hours=6)
        run = save_scenario_to_database(db, scenario_d)

        assert run.id is not None
        assert run.status == "COMPLETED"

        # Query persisted anomaly
        persisted_anom = db.query(AnomalyEvent).filter(AnomalyEvent.anomaly_type == "RESIDUAL_ENERGY_DISCREPANCY").first()
        assert persisted_anom is not None

        # Query persisted case
        persisted_case = db.query(InvestigationCase).filter(InvestigationCase.case_number.like("%CASE%")).first()
        assert persisted_case is not None
        assert len(persisted_case.evidence_records) > 0
    finally:
        db.close()

