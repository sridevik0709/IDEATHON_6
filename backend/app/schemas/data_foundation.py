"""
Pydantic Schemas for Level 2: Data Foundation.
Provides data serialization and contract validation for network assets, readings, scenarios, and cases.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DataSourceSchema(BaseModel):
    id: str
    code: str
    name: str
    source_type: str
    is_active: bool
    is_authorized: bool
    configuration: Dict[str, Any]

    model_config = {"from_attributes": True}


class NetworkAssetSchema(BaseModel):
    id: str
    asset_code: str
    name: str
    asset_type: str
    voltage_class: str
    rated_capacity_kva: Optional[float] = None
    status: str
    location_coordinates: Optional[Dict[str, Any]] = None
    is_simulated: bool

    model_config = {"from_attributes": True}


class HouseholdAggregateMeterSchema(BaseModel):
    id: str
    meter_code: str
    household_count: int
    associated_asset_id: str
    installation_type: str
    phase_configuration: str
    multiplier: float
    is_simulated: bool

    model_config = {"from_attributes": True}


class ConsumptionReadingSchema(BaseModel):
    id: str
    meter_id: str
    timestamp: datetime
    energy_kwh: float
    reactive_energy_kvarh: Optional[float] = None
    interval_minutes: int
    unit: str
    reading_type: str
    validation_status: str
    is_simulated: bool

    model_config = {"from_attributes": True}


class BoundaryReadingSchema(BaseModel):
    id: str
    asset_id: str
    timestamp: datetime
    energy_kwh: float
    power_kw: float
    voltage_v: float
    current_a: float
    power_factor: float
    frequency_hz: float
    unit: str
    boundary_type: str
    validation_status: str
    is_simulated: bool

    model_config = {"from_attributes": True}


class DataQualityResultSchema(BaseModel):
    id: str
    target_type: str
    target_id: str
    quality_dimension: str
    passed: bool
    score: float
    error_code: Optional[str] = None
    diagnostic_message: str
    evaluated_at: datetime
    is_simulated: bool

    model_config = {"from_attributes": True}


class AnomalyEventSchema(BaseModel):
    id: str
    event_code: str
    anomaly_type: str
    severity: str
    related_asset_id: Optional[str] = None
    detected_at: datetime
    time_window_start: datetime
    time_window_end: datetime
    discrepancy_kwh: float
    discrepancy_percent: float
    status: str
    description: str
    is_simulated: bool

    model_config = {"from_attributes": True}


class InvestigationCaseSchema(BaseModel):
    id: str
    case_number: str
    title: str
    priority: str
    status: str
    assigned_role: str
    summary: str
    is_simulated: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ScenarioDescriptor(BaseModel):
    scenario_code: str
    scenario_name: str
    description: str
    documented_inputs: Dict[str, Any]
    expected_outcomes: Dict[str, Any]


class ScenarioExecutionRequest(BaseModel):
    scenario_code: str = Field(..., description="SCENARIO_A, SCENARIO_B, SCENARIO_C, SCENARIO_D, or SCENARIO_E")
    seed: int = Field(default=42, description="RNG seed for mathematical reproducibility")
    persist_to_database: bool = Field(default=True, description="Save generated records into persistent database")


class ScenarioExecutionResponse(BaseModel):
    scenario_code: str
    scenario_name: str
    seed: int
    status: str
    records_generated_count: int
    summary_metrics: Dict[str, Any]
    anomaly_count: int
    cases_generated_count: int
    run_id: Optional[str] = None
    executed_at: datetime

