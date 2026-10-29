"""
Unit and Integration Tests for Energy Accounting Engine & Data Quality Rules.
Level 3: Core Electricity Intelligence.

Tests:
1. Normal accounting (balanced physics losses ~2.8%).
2. Missing readings detection and coverage warnings.
3. Duplicate readings detection.
4. Incorrect downstream mappings (negative loss anomaly).
5. Interval mismatches (mixing 15-min and 60-min intervals).
6. Unit mismatches (non-whitelisted or conflicting units).
7. Nested boundaries (preventing double-counting).
8. Unknown meter identifiers (validation error and 404).
9. Invalid measurements (negative energy, voltage sags/swells).
"""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from app.accounting.data_quality import DataQualityEngine
from app.accounting.engine import EnergyAccountingEngine
from app.accounting.meter_service import MeterIntelligenceService
from app.data_processing.synthetic_generator import (
    SyntheticGridGenerator,
    save_scenario_to_database,
)
from app.database.models import (
    ConsumptionReading,
    DataSource,
    DistributionBoundaryReading,
    HouseholdAggregateMeter,
    NetworkAsset,
    NetworkRelationship,
)


@pytest.fixture(scope="module")
def seeded_db(client):
    """Seed Scenario A into the test database for accounting tests."""
    from app.database.session import SessionLocal
    db = SessionLocal()
    gen = SyntheticGridGenerator(seed=42)
    scenario_a = gen.generate_scenario_a_normal(hours=24)
    save_scenario_to_database(db, scenario_a)
    db.commit()
    yield db
    db.close()


# -----------------------------------------------------------------------------
# 1. Normal Accounting Test
# -----------------------------------------------------------------------------
def test_normal_accounting_balance(seeded_db):
    """Verify normal physical energy reconciliation on Transformer DT-101."""
    dossier = EnergyAccountingEngine.reconcile_boundary(
        db=seeded_db,
        boundary_asset_code="DT-11KV-415V-101",
    )

    assert dossier.boundary_asset_code == "DT-11KV-415V-101"
    assert dossier.energy_entering_boundary_kwh > 0
    assert dossier.recorded_downstream_energy_kwh > 0
    assert dossier.other_accounted_flows_kwh > 0  # Technical loss accounted
    assert dossier.neutral_classification == "NORMAL_TECHNICAL_LOSS"
    assert len(dossier.calculation_steps) == 6
    assert dossier.calculation_steps[0].output_name == "E_in"
    assert dossier.calculation_steps[4].output_name == "E_unaccounted"


# -----------------------------------------------------------------------------
# 2. Missing Readings Detection
# -----------------------------------------------------------------------------
def test_missing_readings_detection():
    """Verify audit engine detects missing intervals and reports coverage."""
    now = datetime.now(timezone.utc)
    # Only 10 readings out of expected 24
    timestamps = [now - timedelta(hours=i) for i in range(10)]
    findings = DataQualityEngine.audit_coverage_and_missing(
        timestamps=timestamps,
        target_name="MTR-TEST-MISSING",
        expected_count=24,
    )

    codes = [f.rule_code for f in findings]
    assert "WARN_INSUFFICIENT_COVERAGE" in codes


# -----------------------------------------------------------------------------
# 3. Duplicate Readings Detection
# -----------------------------------------------------------------------------
def test_duplicate_readings_detection():
    """Verify duplicate timestamps are intercepted."""
    now = datetime.now(timezone.utc)
    records = [
        {"timestamp": now, "energy_kwh": 1.5},
        {"timestamp": now, "energy_kwh": 1.5},  # Duplicate
        {"timestamp": now - timedelta(hours=1), "energy_kwh": 2.0},
    ]
    findings = DataQualityEngine.audit_duplicates(records, "MTR-TEST-DUP")
    assert any(f.rule_code == "ERR_DUPLICATE_INTERVAL_RECORD" for f in findings)


# -----------------------------------------------------------------------------
# 4. Incorrect Mapping (Negative Loss Anomaly)
# -----------------------------------------------------------------------------
def test_incorrect_mapping_negative_loss():
    """Verify topology audit detects downstream consumption exceeding upstream boundary."""
    from app.database.models import NetworkAsset, DistributionBoundaryReading, HouseholdAggregateMeter, ConsumptionReading
    from unittest.mock import MagicMock

    mock_asset = MagicMock(spec=NetworkAsset)
    mock_asset.asset_code = "DT-MOCK-MAPPING"
    mock_asset.asset_type = "TRANSFORMER"

    # Upstream recorded 100 kWh
    br = MagicMock(spec=DistributionBoundaryReading)
    br.boundary_type = "INPUT"
    br.energy_kwh = 100.0

    # Downstream meters recorded 150 kWh (50% excess!)
    cr = MagicMock(spec=ConsumptionReading)
    cr.energy_kwh = 150.0

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()

    findings = DataQualityEngine.audit_boundary_topology(
        db=mock_db,
        boundary_asset=mock_asset,
        boundary_readings=[br],
        downstream_meters=[MagicMock()],
        downstream_readings=[cr],
    )

    assert any(f.rule_code == "ERR_INCORRECT_DOWNSTREAM_ASSET_MAPPING" for f in findings)


# -----------------------------------------------------------------------------
# 5. Interval Mismatch Detection
# -----------------------------------------------------------------------------
def test_interval_mismatch_detection():
    """Verify mixing 15-minute and 60-minute interval readings raises warning."""
    intervals = [60, 60, 15, 60, 15]
    findings = DataQualityEngine.audit_intervals(intervals, "MTR-TEST-INTERVAL", expected_interval=60)
    assert any(f.rule_code == "ERR_INTERVAL_MISMATCH" for f in findings)


# -----------------------------------------------------------------------------
# 6. Unit Mismatch Detection
# -----------------------------------------------------------------------------
def test_unit_mismatch_detection():
    """Verify non-standard units (e.g., MWh, BTU) are flagged."""
    units = ["KWH", "MWH", "BTU"]
    findings = DataQualityEngine.audit_units(units, "MTR-TEST-UNITS", expected_unit="KWH")
    assert any(f.rule_code == "ERR_UNIT_NON_WHITELISTED" for f in findings)


# -----------------------------------------------------------------------------
# 7. Nested Boundaries (Anti-Double-Counting)
# -----------------------------------------------------------------------------
def test_nested_boundaries_anti_double_counting(seeded_db):
    """
    Verify Feeder boundary reconciliation sums only child transformer inputs,
    and does NOT double-count downstream meters.
    """
    dossier = EnergyAccountingEngine.reconcile_boundary(
        db=seeded_db,
        boundary_asset_code="FDR-33KV-F1",
    )

    assert dossier.boundary_asset_code == "FDR-33KV-F1"
    assert dossier.boundary_asset_type == "FEEDER"
    # Downstream entities must be child transformers
    for source in dossier.source_measurements:
        assert source.entity_type == "CHILD_TRANSFORMER_BOUNDARY_INPUT"


# -----------------------------------------------------------------------------
# 8. Unknown Meter Identifiers (Validation & 404)
# -----------------------------------------------------------------------------
def test_unknown_meter_lookup_404(client):
    """Verify requesting an unknown meter returns standardized 404 envelope."""
    response = client.get("/api/v1/meters/MTR-UNKNOWN-999")
    assert response.status_code == 404
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "ERR_METER_NOT_FOUND"
    assert "not found" in payload["error"]["message"].lower()


def test_invalid_meter_format_400(client):
    """Verify malformed meter code returns 400 Bad Request."""
    response = client.get("/api/v1/meters/invalid!!code")
    assert response.status_code == 400
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "ERR_INVALID_METER_FORMAT"


# -----------------------------------------------------------------------------
# 9. Invalid Measurements (Negative Energy & Voltage Spikes)
# -----------------------------------------------------------------------------
def test_invalid_measurements_plausibility():
    """Verify negative energy and extreme voltage are flagged."""
    readings = [
        {"energy_kwh": -25.0, "voltage_v": 240.0},
        {"energy_kwh": 3.0, "voltage_v": 298.0},  # Voltage swell
        {"energy_kwh": 2.0, "voltage_v": 150.0},  # Voltage sag
    ]
    findings = DataQualityEngine.audit_plausibility(readings, "MTR-TEST-PLAUSIBLE")
    codes = [f.rule_code for f in findings]
    assert "ERR_ENERGY_NEGATIVE" in codes
    assert "ERR_VOLTAGE_SWELL" in codes
    assert "WARN_VOLTAGE_SAG" in codes


# -----------------------------------------------------------------------------
# 10. Known Meter Lookup & Aggregate Consumption Endpoint
# -----------------------------------------------------------------------------
def test_known_meter_lookup_success(client, seeded_db):
    """Verify valid demo meter lookup succeeds and contains anti-surveillance compliance notice."""
    response = client.get("/api/v1/meters/AGG-MTR-DT101-A")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["meter_code"] == "AGG-MTR-DT101-A"
    assert data["household_count"] > 1
    assert "disclaimer" in data
    assert "appliance" in data["disclaimer"].lower()


def test_meter_consumption_profile(client, seeded_db):
    """Verify consumption profile returns trend series, statistics, and quality findings."""
    response = client.get("/api/v1/meters/AGG-MTR-DT101-A/consumption")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["meter_code"] == "AGG-MTR-DT101-A"
    assert "total_consumption_kwh" in data
    assert "trend_series" in data
    assert "compliance_notice" in data
