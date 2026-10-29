"""
Pydantic Schemas for Level 3: Core Electricity Intelligence.
Validation models for Meter Lookup, Aggregate Consumption, and Discrepancy Explorer.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MeterLookupSchema(BaseModel):
    meter_id: str
    meter_code: str
    household_count: int
    associated_asset_id: Optional[str] = None
    associated_asset_code: Optional[str] = None
    associated_asset_name: Optional[str] = None
    associated_asset_type: Optional[str] = None
    installation_type: str
    phase_configuration: str
    multiplier: float
    data_source_code: str
    data_source_type: str
    data_source_authorized: bool
    is_simulated: bool
    disclaimer: str


class ConsumptionTrendItemSchema(BaseModel):
    timestamp: str
    energy_kwh: float
    peak_power_kw: Optional[float] = None
    is_unusual: bool = False
    unusual_reason: Optional[str] = None


class QualityFindingSchema(BaseModel):
    rule_code: str
    dimension: str
    severity: str
    passed: bool
    diagnostic_message: str
    target_entity: str
    details: Optional[Dict[str, Any]] = None
    recommended_action: Optional[str] = None


class MeterConsumptionProfileSchema(BaseModel):
    meter_code: str
    household_count: int
    analysis_period_start: str
    analysis_period_end: str
    total_consumption_kwh: float
    average_hourly_kwh: float
    peak_power_kw: float
    minimum_interval_kwh: float
    maximum_interval_kwh: float
    readings_count: int
    expected_readings_count: int
    missing_intervals_count: int
    missing_timestamps: List[str] = []
    unusual_changes_count: int
    data_quality_warnings: List[QualityFindingSchema]
    trend_series: List[ConsumptionTrendItemSchema]
    compliance_notice: str


class CalculationStepSchema(BaseModel):
    step_number: int
    title: str
    formula: str
    inputs: Dict[str, Any]
    output_name: str
    output_value: float
    unit: str
    explanation: str


class SourceMeasurementTraceSchema(BaseModel):
    entity_code: str
    entity_type: str
    readings_count: int
    total_energy_kwh: float
    unit: str
    interval_minutes: int
    validation_status: str
    data_source: str
    is_simulated: bool


class ReconciliationRequest(BaseModel):
    boundary_asset_code: str = Field(..., description="Target boundary asset code (e.g., 'DT-11KV-415V-101', 'FDR-33KV-F1', 'SUB-132KV-NORTH')")
    start_time: Optional[datetime] = Field(None, description="Start of measurement window (ISO 8601 UTC)")
    end_time: Optional[datetime] = Field(None, description="End of measurement window (ISO 8601 UTC)")
    custom_technical_loss_pct: Optional[float] = Field(None, ge=0.0, le=20.0, description="Optional custom physics technical loss model percentage (default 2.8%)")


class ReconciliationResponse(BaseModel):
    boundary_asset_code: str
    boundary_asset_name: str
    boundary_asset_type: str
    voltage_class: str
    time_window_start: str
    time_window_end: str
    total_expected_intervals: int
    total_actual_intervals: int
    missing_intervals_count: int
    energy_entering_boundary_kwh: float
    recorded_downstream_energy_kwh: float
    other_accounted_flows_kwh: float
    gross_discrepancy_kwh: float
    unaccounted_energy_kwh: float
    discrepancy_percentage: float
    sensor_uncertainty_kwh: float
    remaining_uncertainty_percent: float
    neutral_classification: str
    classification_reason: str
    calculation_steps: List[CalculationStepSchema]
    source_measurements: List[SourceMeasurementTraceSchema]
    data_quality_findings: List[QualityFindingSchema]
    reproducibility_hash: str


class AccountingBoundaryItemSchema(BaseModel):
    asset_code: str
    name: str
    asset_type: str
    voltage_class: str
    rated_capacity_kva: float
    child_entities_count: int
    child_type: str
    status: str

