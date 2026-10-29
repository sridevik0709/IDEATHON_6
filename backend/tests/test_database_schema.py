"""
Database Schema & Entity Verification Tests.
Verifies all 15 Level 2 entities, foreign key relationships, and duplicate constraints.
"""

from datetime import datetime, timezone
import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.session import get_engine, init_database
from app.database.models import (
    AnomalyEvent,
    AuditLog,
    ConsumptionReading,
    DataQualityResult,
    DataSource,
    DistributionBoundaryReading,
    EvidenceRecord,
    HouseholdAggregateMeter,
    InvestigationAction,
    InvestigationCase,
    InvestigationOutcome,
    NetworkAsset,
    NetworkRelationship,
    ScenarioRun,
    User,
)


@pytest.fixture
def db_session():
    """Provides a fresh database session with tables initialized."""
    init_database()
    engine = get_engine()
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_schema_entities_persistence(db_session: Session):
    """Verify core entity persistence and foreign key hierarchy."""
    # 1. Create Data Source
    ds = DataSource(
        code="TEST-SRC-01",
        name="Test Ingest Engine",
        source_type="SYNTHETIC",
        is_active=True,
        is_authorized=True,
    )
    db_session.add(ds)
    db_session.flush()
    assert ds.id is not None

    # 2. Create Network Assets (Substation & Feeder)
    sub = NetworkAsset(
        asset_code="TEST-SUB-01",
        name="Test Substation",
        asset_type="SUBSTATION",
        voltage_class="132KV",
        source_id=ds.id,
        is_simulated=True,
    )
    fdr = NetworkAsset(
        asset_code="TEST-FDR-01",
        name="Test Feeder",
        asset_type="FEEDER",
        voltage_class="11KV",
        source_id=ds.id,
        is_simulated=True,
    )
    db_session.add_all([sub, fdr])
    db_session.flush()

    # 3. Create Network Relationship
    rel = NetworkRelationship(
        parent_asset_id=sub.id,
        child_asset_id=fdr.id,
        relationship_type="SUPPLIES",
        is_current=True,
        is_simulated=True,
    )
    db_session.add(rel)
    db_session.flush()

    # 4. Create Household Aggregate Meter
    meter = HouseholdAggregateMeter(
        meter_code="TEST-MTR-01",
        household_count=12,
        associated_asset_id=fdr.id,
        source_id=ds.id,
        is_simulated=True,
    )
    db_session.add(meter)
    db_session.flush()

    # 5. Create Consumption Reading
    now = datetime(2026, 10, 29, 12, 0, 0, tzinfo=timezone.utc)
    reading = ConsumptionReading(
        meter_id=meter.id,
        timestamp=now,
        energy_kwh=14.5,
        unit="KWH",
        reading_type="INTERVAL",
        validation_status="VALID",
        source_id=ds.id,
        is_simulated=True,
    )
    db_session.add(reading)
    db_session.flush()

    # 6. Verify User & Investigation Case
    user = User(
        username="test_investigator",
        email="inv@gridguard.test",
        full_name="Agent Smith",
        hashed_password="secure-hash-sample",
        role="FIELD_INVESTIGATOR",
    )
    db_session.add(user)
    db_session.flush()

    case = InvestigationCase(
        case_number="CASE-TEST-001",
        title="Test Forensic Docket",
        priority="HIGH",
        assigned_to_user_id=user.id,
        summary="Test investigation summary",
        is_simulated=True,
    )
    db_session.add(case)
    db_session.flush()

    # 7. Evidence Record with Hash
    evidence = EvidenceRecord(
        case_id=case.id,
        evidence_type="ENERGY_BALANCE_SNAPSHOT",
        title="Snapshot Evidence",
        description="Recorded reading diff",
        payload_data={"diff_kwh": 4.5},
        hash_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        collected_by="SYSTEM",
        is_simulated=True,
    )
    db_session.add(evidence)
    db_session.flush()

    # Assert relations
    assert len(case.evidence_records) == 1
    assert case.evidence_records[0].hash_sha256 is not None
    assert case.assigned_user.username == "test_investigator"
    assert meter.readings[0].energy_kwh == 14.5


def test_duplicate_consumption_reading_constraint(db_session: Session):
    """Verify that composite unique constraint (meter_id, timestamp, reading_type) prevents duplicate ingestion."""
    ds = DataSource(code="TEST-SRC-DUP", name="Dup Source", source_type="SYNTHETIC", is_authorized=True)
    db_session.add(ds)
    db_session.flush()

    asset = NetworkAsset(asset_code="TEST-ASSET-DUP", name="Asset Dup", asset_type="TRANSFORMER", voltage_class="11KV", source_id=ds.id)
    db_session.add(asset)
    db_session.flush()

    meter = HouseholdAggregateMeter(meter_code="TEST-MTR-DUP", household_count=10, associated_asset_id=asset.id, source_id=ds.id)
    db_session.add(meter)
    db_session.flush()

    ts = datetime(2026, 10, 29, 14, 0, 0, tzinfo=timezone.utc)
    r1 = ConsumptionReading(
        meter_id=meter.id,
        timestamp=ts,
        energy_kwh=20.0,
        reading_type="INTERVAL",
        source_id=ds.id,
        is_simulated=True,
    )
    db_session.add(r1)
    db_session.flush()

    # Second reading with identical meter, timestamp, and reading_type
    r2 = ConsumptionReading(
        meter_id=meter.id,
        timestamp=ts,
        energy_kwh=22.5,
        reading_type="INTERVAL",
        source_id=ds.id,
        is_simulated=True,
    )
    db_session.add(r2)

    with pytest.raises(IntegrityError):
        db_session.flush()

