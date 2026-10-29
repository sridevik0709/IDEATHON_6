"""
Data Integrity and Quality Audit Engine Tests.
Verifies rejection of invalid records, duplicate detection, and source provenance.
"""

from datetime import datetime, timedelta, timezone
from app.data_processing.quality_rules import (
    audit_boundary_record,
    audit_consumption_record,
    detect_duplicates,
)
from app.data_processing.sources.synthetic import SyntheticDataSourceAdapter
from app.data_processing.sources.utility import UtilityIntegrationAdapter


def test_audit_detects_negative_energy():
    """Verify that negative energy reading produces ERR_NEGATIVE_ENERGY finding."""
    record = {
        "unit": "KWH",
        "timestamp": datetime(2026, 10, 29, 10, 0, tzinfo=timezone.utc),
        "energy_kwh": -12.4,
        "is_simulated": True,
    }
    findings = audit_consumption_record(record)
    error_codes = [f.error_code for f in findings if not f.passed]
    assert "ERR_NEGATIVE_ENERGY" in error_codes


def test_audit_detects_future_timestamp():
    """Verify that future timestamp beyond allowable skew produces ERR_TIMESTAMP_FUTURE."""
    future_time = datetime.now(timezone.utc) + timedelta(days=5)
    record = {
        "unit": "KWH",
        "timestamp": future_time,
        "energy_kwh": 18.2,
        "is_simulated": True,
    }
    findings = audit_consumption_record(record)
    error_codes = [f.error_code for f in findings if not f.passed]
    assert "ERR_TIMESTAMP_FUTURE" in error_codes


def test_audit_detects_invalid_unit():
    """Verify that unrecognized unit produces ERR_INVALID_UNIT."""
    record = {
        "unit": "GALLONS",
        "timestamp": datetime(2026, 10, 29, 10, 0, tzinfo=timezone.utc),
        "energy_kwh": 25.0,
        "is_simulated": True,
    }
    findings = audit_consumption_record(record)
    error_codes = [f.error_code for f in findings if not f.passed]
    assert "ERR_INVALID_UNIT" in error_codes


def test_audit_detects_voltage_spike():
    """Verify that severe overvoltage on secondary boundary produces ERR_VOLTAGE_SPIKE."""
    record = {
        "unit": "KWH",
        "timestamp": datetime(2026, 10, 29, 10, 0, tzinfo=timezone.utc),
        "energy_kwh": 50.0,
        "voltage_v": 520.0,
        "boundary_type": "TRANSFORMER_SECONDARY",
        "is_simulated": True,
    }
    findings = audit_boundary_record(record)
    error_codes = [f.error_code for f in findings if not f.passed]
    assert "ERR_VOLTAGE_SPIKE" in error_codes


def test_duplicate_record_detection():
    """Verify duplicate detection identifies collisions on composite key (meter_id, timestamp, reading_type)."""
    ts = datetime(2026, 10, 29, 10, 0, tzinfo=timezone.utc)
    records = [
        {"id": "rec-1", "meter_id": "MTR-01", "timestamp": ts, "reading_type": "INTERVAL"},
        {"id": "rec-2", "meter_id": "MTR-02", "timestamp": ts, "reading_type": "INTERVAL"},
        {"id": "rec-3", "meter_id": "MTR-01", "timestamp": ts, "reading_type": "INTERVAL"},  # Duplicate of rec-1
    ]
    dups = detect_duplicates(records, key_fields=("meter_id", "timestamp", "reading_type"))
    assert "rec-3" in dups or "('MTR-01', datetime.datetime(2026, 10, 29, 10, 0, tzinfo=datetime.timezone.utc), 'INTERVAL')" in str(dups)


def test_data_source_adapters_contract():
    """Verify data source common interface and strict restriction on utility adapter."""
    # 1. Synthetic adapter is operational & authorized
    synth = SyntheticDataSourceAdapter()
    assert synth.is_operational() is True
    assert synth.is_authorized is True
    assert synth.get_provenance_metadata()["is_simulated"] is True

    # 2. Utility adapter is strictly unconfigured and unauthorized
    utility = UtilityIntegrationAdapter()
    assert utility.is_operational() is False
    assert utility.is_authorized is False
    health = utility.health_check()
    assert health["status"] == "UNCONFIGURED_PENDING_UTILITY_AUTHORIZATION"

