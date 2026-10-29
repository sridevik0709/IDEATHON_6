"""
SQLAlchemy Persistent Domain Models for GridGuard Nexus X.
Level 2: Data Foundation.

Enforces 15 core entities:
1. DataSource
2. NetworkAsset
3. NetworkRelationship
4. HouseholdAggregateMeter
5. ConsumptionReading
6. DistributionBoundaryReading
7. DataQualityResult
8. AnomalyEvent
9. InvestigationCase
10. EvidenceRecord
11. InvestigationAction
12. InvestigationOutcome
13. ScenarioRun
14. AuditLog
15. User
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database.base import Base, TimestampMixin

# Use JSON with JSONB fallback for cross-dialect compatibility (PostgreSQL JSONB / SQLite JSON)
JSONType = JSON().with_variant(JSONB, "postgresql")


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ==============================================================================
# 1. Users and Authentication
# ==============================================================================
class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="GRID_ANALYST", nullable=False)  # ADMIN, GRID_ANALYST, FIELD_INVESTIGATOR, AUDITOR
    permissions: Mapped[dict] = mapped_column(JSONType, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    assigned_cases: Mapped[List["InvestigationCase"]] = relationship("InvestigationCase", back_populates="assigned_user")


# ==============================================================================
# 2. Data Sources
# ==============================================================================
class DataSource(Base, TimestampMixin):
    __tablename__ = "data_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)  # SYNTHETIC, LOCAL_FILE, UTILITY_SCADA, UTILITY_MDMS
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_authorized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    configuration: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)

    # Relationships
    assets: Mapped[List["NetworkAsset"]] = relationship("NetworkAsset", back_populates="source")
    meters: Mapped[List["HouseholdAggregateMeter"]] = relationship("HouseholdAggregateMeter", back_populates="source")


# ==============================================================================
# 3. Network Assets
# ==============================================================================
class NetworkAsset(Base, TimestampMixin):
    __tablename__ = "network_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    asset_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # SUBSTATION, FEEDER, TRANSFORMER, FEEDER_PILLAR
    voltage_class: Mapped[str] = mapped_column(String(32), nullable=False)  # 132KV, 33KV, 11KV, 415V, 230V
    rated_capacity_kva: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="OPERATIONAL", nullable=False)
    location_coordinates: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("data_sources.id"), nullable=False)

    # Relationships
    source: Mapped["DataSource"] = relationship("DataSource", back_populates="assets")
    parent_links: Mapped[List["NetworkRelationship"]] = relationship(
        "NetworkRelationship",
        foreign_keys="NetworkRelationship.child_asset_id",
        back_populates="child_asset"
    )
    child_links: Mapped[List["NetworkRelationship"]] = relationship(
        "NetworkRelationship",
        foreign_keys="NetworkRelationship.parent_asset_id",
        back_populates="parent_asset"
    )
    boundary_readings: Mapped[List["DistributionBoundaryReading"]] = relationship("DistributionBoundaryReading", back_populates="asset")
    aggregate_meters: Mapped[List["HouseholdAggregateMeter"]] = relationship("HouseholdAggregateMeter", back_populates="associated_asset")


# ==============================================================================
# 4. Network Relationships (Topology Hierarchy)
# ==============================================================================
class NetworkRelationship(Base, TimestampMixin):
    __tablename__ = "network_relationships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    parent_asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("network_assets.id"), nullable=False, index=True)
    child_asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("network_assets.id"), nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(String(32), default="SUPPLIES", nullable=False)  # SUPPLIES, CONNECTED_TO, MONITORS
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    # Relationships
    parent_asset: Mapped["NetworkAsset"] = relationship("NetworkAsset", foreign_keys=[parent_asset_id], back_populates="child_links")
    child_asset: Mapped["NetworkAsset"] = relationship("NetworkAsset", foreign_keys=[child_asset_id], back_populates="parent_links")


# ==============================================================================
# 5. Household Aggregate Meters
# ==============================================================================
class HouseholdAggregateMeter(Base, TimestampMixin):
    __tablename__ = "household_aggregate_meters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    meter_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    household_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    associated_asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("network_assets.id"), nullable=False, index=True)
    installation_type: Mapped[str] = mapped_column(String(48), default="AGGREGATE_CONSUMER_CLUSTER", nullable=False)
    phase_configuration: Mapped[str] = mapped_column(String(24), default="THREE_PHASE", nullable=False)
    multiplier: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("data_sources.id"), nullable=False)

    # Relationships
    source: Mapped["DataSource"] = relationship("DataSource", back_populates="meters")
    associated_asset: Mapped["NetworkAsset"] = relationship("NetworkAsset", back_populates="aggregate_meters")
    readings: Mapped[List["ConsumptionReading"]] = relationship("ConsumptionReading", back_populates="meter")


# ==============================================================================
# 6. Consumption Readings (Time-series Downstream)
# ==============================================================================
class ConsumptionReading(Base, TimestampMixin):
    __tablename__ = "consumption_readings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    meter_id: Mapped[str] = mapped_column(String(36), ForeignKey("household_aggregate_meters.id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    energy_kwh: Mapped[float] = mapped_column(Float, nullable=False)
    reactive_energy_kvarh: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    peak_power_kw: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    interval_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    unit: Mapped[str] = mapped_column(String(16), default="KWH", nullable=False)
    reading_type: Mapped[str] = mapped_column(String(32), default="INTERVAL", nullable=False)  # INTERVAL, ESTIMATED, BACKFILLED
    validation_status: Mapped[str] = mapped_column(String(32), default="VALID", nullable=False, index=True)  # VALID, INVALID, SUSPECT, DELAYED
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("data_sources.id"), nullable=False)

    # Relationships
    meter: Mapped["HouseholdAggregateMeter"] = relationship("HouseholdAggregateMeter", back_populates="readings")

    __table_args__ = (
        UniqueConstraint("meter_id", "timestamp", "reading_type", name="uq_meter_timestamp_reading_type"),
        Index("idx_consumption_meter_time", "meter_id", "timestamp"),
    )


# ==============================================================================
# 7. Distribution Boundary Energy Readings
# ==============================================================================
class DistributionBoundaryReading(Base, TimestampMixin):
    __tablename__ = "distribution_boundary_readings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    asset_id: Mapped[str] = mapped_column(String(36), ForeignKey("network_assets.id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    energy_kwh: Mapped[float] = mapped_column(Float, nullable=False)
    power_kw: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    voltage_v: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    current_a: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    power_factor: Mapped[float] = mapped_column(Float, default=0.95, nullable=False)
    frequency_hz: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    unit: Mapped[str] = mapped_column(String(16), default="KWH", nullable=False)
    boundary_type: Mapped[str] = mapped_column(String(32), nullable=False)  # SUBSTATION_OUTFLOW, FEEDER_HEAD, TRANSFORMER_PRIMARY_INPUT
    validation_status: Mapped[str] = mapped_column(String(32), default="VALID", nullable=False, index=True)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("data_sources.id"), nullable=False)

    # Relationships
    asset: Mapped["NetworkAsset"] = relationship("NetworkAsset", back_populates="boundary_readings")

    __table_args__ = (
        UniqueConstraint("asset_id", "timestamp", "boundary_type", name="uq_asset_time_boundary"),
        Index("idx_boundary_asset_time", "asset_id", "timestamp"),
    )


# ==============================================================================
# 8. Data Quality Results
# ==============================================================================
class DataQualityResult(Base, TimestampMixin):
    __tablename__ = "data_quality_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)  # CONSUMPTION_READING, BOUNDARY_READING, BATCH_INGEST
    target_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    quality_dimension: Mapped[str] = mapped_column(String(32), nullable=False)  # COMPLETENESS, TIMELINESS, PLAUSIBILITY, CONSISTENCY, INTEGRITY
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # ERR_NEGATIVE_ENERGY, ERR_VOLTAGE_SPIKE, ERR_TIMESTAMP_DRIFT
    diagnostic_message: Mapped[str] = mapped_column(Text, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("idx_quality_target", "target_type", "target_id"),
    )


# ==============================================================================
# 9. Anomaly Events
# ==============================================================================
class AnomalyEvent(Base, TimestampMixin):
    __tablename__ = "anomaly_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    event_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    anomaly_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # RESIDUAL_ENERGY_DISCREPANCY, TOPOLOGY_MAPPING_ERROR, DELAYED_READING_ACCUMULATION
    severity: Mapped[str] = mapped_column(String(16), default="MEDIUM", nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    related_asset_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("network_assets.id"), nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    time_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    time_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    discrepancy_kwh: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    discrepancy_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="DETECTED", nullable=False)  # DETECTED, UNDER_INVESTIGATION, RESOLVED, FALSE_POSITIVE
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    cases: Mapped[List["InvestigationCase"]] = relationship("InvestigationCase", back_populates="primary_anomaly")


# ==============================================================================
# 10. Investigation Cases
# ==============================================================================
class InvestigationCase(Base, TimestampMixin):
    __tablename__ = "investigation_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default="MEDIUM", nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    status: Mapped[str] = mapped_column(String(32), default="OPEN", nullable=False, index=True)  # OPEN, TRIAGE, FIELD_DISPATCHED, RESOLVED, CLOSED
    primary_anomaly_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("anomaly_events.id"), nullable=True)
    target_asset_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("network_assets.id"), nullable=True)
    assigned_to_user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    assigned_role: Mapped[str] = mapped_column(String(32), default="GRID_ANALYST", nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    primary_anomaly: Mapped[Optional["AnomalyEvent"]] = relationship("AnomalyEvent", back_populates="cases")
    assigned_user: Mapped[Optional["User"]] = relationship("User", back_populates="assigned_cases")
    evidence_records: Mapped[List["EvidenceRecord"]] = relationship("EvidenceRecord", back_populates="case", cascade="all, delete-orphan")
    actions: Mapped[List["InvestigationAction"]] = relationship("InvestigationAction", back_populates="case", cascade="all, delete-orphan")
    outcome: Mapped[Optional["InvestigationOutcome"]] = relationship("InvestigationOutcome", back_populates="case", uselist=False, cascade="all, delete-orphan")


# ==============================================================================
# 11. Evidence Records
# ==============================================================================
class EvidenceRecord(Base, TimestampMixin):
    __tablename__ = "evidence_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigation_cases.id"), nullable=False, index=True)
    evidence_type: Mapped[str] = mapped_column(String(48), nullable=False)  # ENERGY_BALANCE_SNAPSHOT, TOPOLOGY_TRACE, METER_TAMPER_RECORD
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    payload_data: Mapped[dict] = mapped_column(JSONType, nullable=False)
    hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    collected_by: Mapped[str] = mapped_column(String(64), nullable=False)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    case: Mapped["InvestigationCase"] = relationship("InvestigationCase", back_populates="evidence_records")


# ==============================================================================
# 12. Investigation Actions
# ==============================================================================
class InvestigationAction(Base, TimestampMixin):
    __tablename__ = "investigation_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigation_cases.id"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(48), nullable=False)  # TOPOLOGY_VERIFICATION, FIELD_INSPECTION_DISPATCH, METER_TESTING
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)  # PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    performed_by: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False)
    action_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    case: Mapped["InvestigationCase"] = relationship("InvestigationCase", back_populates="actions")


# ==============================================================================
# 13. Investigation Outcomes
# ==============================================================================
class InvestigationOutcome(Base, TimestampMixin):
    __tablename__ = "investigation_outcomes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    case_id: Mapped[str] = mapped_column(String(36), ForeignKey("investigation_cases.id"), unique=True, nullable=False, index=True)
    outcome_type: Mapped[str] = mapped_column(String(64), nullable=False)  # CONFIRMED_NON_TECHNICAL_LOSS, TECHNICAL_FAULT_CORRECTED, GIS_MAPPING_ERROR_RECTIFIED
    estimated_loss_kwh: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    estimated_financial_loss_inr: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    action_taken: Mapped[str] = mapped_column(Text, nullable=False)
    closed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    closed_by: Mapped[str] = mapped_column(String(64), nullable=False)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    case: Mapped["InvestigationCase"] = relationship("InvestigationCase", back_populates="outcome")


# ==============================================================================
# 14. Scenario Runs
# ==============================================================================
class ScenarioRun(Base, TimestampMixin):
    __tablename__ = "scenario_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    scenario_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # SCENARIO_A, SCENARIO_B, SCENARIO_C, SCENARIO_D, SCENARIO_E
    scenario_name: Mapped[str] = mapped_column(String(128), nullable=False)
    seed: Mapped[int] = mapped_column(Integer, default=42, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="RUNNING", nullable=False)  # RUNNING, COMPLETED, FAILED
    parameters: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    records_generated_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary_metrics: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


# ==============================================================================
# 15. Audit Logs
# ==============================================================================
class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    actor_id: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(32), default="SYSTEM", nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # RUN_SCENARIO, CREATE_CASE, DISPATCH_PROBE
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    details: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

