"""
Pydantic Schemas for Level 5: Evidence Traceability and What-If Analysis.

Provides validation models for:
- Interactive Evidence Investigation Graph (Nodes, Edges, Visual States)
- Node Inspection Docket (Source ID, Timestamp, Measurement, Calculation, Evidence, Rules, Verification Status)
- What-If Simulation Scenarios (Delayed Telemetry, Interval Alignment, Mapping Corrections, Duplicate Removal, DQ Fixes)
- Before-and-After Comparison Dossier (Inputs, Original vs Revised Accounting, Deltas, Hypotheses Shifts, Data Protection)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GraphNodeSchema(BaseModel):
    node_id: str = Field(..., description="Unique node identifier (e.g. NODE_DISC_01, NODE_SRC_01)")
    node_type: str = Field(..., description="DISCREPANCY_ROOT, SOURCE_MEASUREMENT, DATA_QUALITY_FINDING, HYPOTHESIS_EXPLANATION, VERIFICATION_ACTION, INVESTIGATION_OUTCOME")
    visual_state: str = Field(..., description="OBSERVED_EVIDENCE, CALCULATED_FINDING, HYPOTHESIS, RECOMMENDATION, CONFIRMED_OUTCOME")
    label: str = Field(..., description="Primary node title / label")
    subtitle: Optional[str] = Field(None, description="Secondary context or asset identifier")
    entity_code: Optional[str] = Field(None, description="Associated physical asset or meter code")
    timestamp_or_period: Optional[str] = Field(None, description="Associated timestamp or time interval")
    metric_value: Optional[Any] = Field(None, description="Quantified measurement or calculated numerical value")
    unit: Optional[str] = Field(None, description="Physical unit of measurement (KWH, %, V, etc.)")
    data_status: str = Field(..., description="VALID, SIMULATED, BUFFERED_DELAYED, CORRUPTED, FLAGGED, HYPOTHETICAL")
    calculation_formula: Optional[str] = Field(None, description="Mathematical equation or audit logic that produced this node")
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="IDs of concrete evidence items supporting this node")
    missing_evidence_list: List[str] = Field(default_factory=list, description="Missing telemetry items or data gaps")
    reasoning_rule: Optional[str] = Field(None, description="Governing rule code or engineering standard (e.g. RULE_DQ_001, CLASS_0.5_TOLERANCE)")
    verification_status: str = Field(..., description="VERIFIED, PENDING_FIELD_CHECK, DISPROVEN, SIMULATED_ONLY")
    is_simulated: bool = Field(True, description="True if based on synthetic demonstration data or hypothetical assumption")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary inspectable attributes")


class GraphEdgeSchema(BaseModel):
    edge_id: str = Field(..., description="Unique edge identifier")
    source_node_id: str = Field(..., description="Source node identifier")
    target_node_id: str = Field(..., description="Target node identifier")
    relationship_type: str = Field(..., description="DERIVED_FROM, AUDITED_BY, INFORMS, EXPLAINED_BY, RECOMMENDS, LEADS_TO")
    label: str = Field(..., description="Readable edge relationship label")
    is_dashed: bool = Field(False, description="True if relationship is hypothetical or pending verification")


class InvestigationGraphResponse(BaseModel):
    boundary_asset_code: str
    boundary_asset_name: str
    voltage_class: str
    analysis_period_start: str
    analysis_period_end: str
    nodes: List[GraphNodeSchema]
    edges: List[GraphEdgeSchema]
    summary: Dict[str, Any] = Field(default_factory=dict)
    generated_at: str


class WhatIfCorrectionRequest(BaseModel):
    boundary_asset_code: str = Field(..., description="Target boundary asset code (e.g. 'DT-11KV-415V-101', 'FDR-33KV-F1')")
    scenario_type: str = Field(..., description="DELAYED_READINGS_ARRIVED, ALIGN_MEASUREMENT_INTERVALS, CORRECT_TOPOLOGICAL_MAPPING, REMOVE_DUPLICATE_RECORDS, CORRECT_DATA_QUALITY_ISSUES, CUSTOM_ASSUMPTION")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Scenario-specific parameter overrides")
    simulated_provenance: str = Field("HYPOTHETICAL_SIMULATION", description="HYPOTHETICAL_SIMULATION, SIMULATED_TEST_CORRECTION, ACTUAL_UTILITY_CORRECTION")


class AccountingDeltaSchema(BaseModel):
    energy_entering_kwh: float
    recorded_downstream_kwh: float
    other_accounted_flows_kwh: float
    gross_discrepancy_kwh: float
    unaccounted_energy_kwh: float
    discrepancy_percentage: float
    neutral_classification: str
    classification_reason: str


class DifferenceSummarySchema(BaseModel):
    delta_unaccounted_kwh: float
    delta_discrepancy_pct: float
    delta_downstream_kwh: float
    delta_technical_loss_kwh: float
    classification_changed: bool
    original_classification: str
    revised_classification: str
    discrepancy_resolved: bool


class DataProtectionGuaranteeSchema(BaseModel):
    original_records_unmodified: bool = Field(True, description="Certified that zero database rows in production telemetry tables were changed")
    scenario_run_id: str = Field(..., description="Isolated ScenarioRun ID where hypothetical results are stored separately")
    correction_provenance: str = Field(..., description="HYPOTHETICAL_SIMULATION, SIMULATED_TEST_CORRECTION, ACTUAL_UTILITY_CORRECTION")
    real_case_auto_resolution_prevented: bool = Field(True, description="Strict constraint: hypothetical corrections cannot close real field cases")
    audit_notice: str = Field(..., description="Forensic integrity guarantee statement")


class BeforeAfterComparisonResponse(BaseModel):
    boundary_asset_code: str
    boundary_asset_name: str
    scenario_type: str
    scenario_title: str
    assumption_description: str
    original_accounting: AccountingDeltaSchema
    revised_accounting: AccountingDeltaSchema
    differences: DifferenceSummarySchema
    original_quality_warnings_count: int
    revised_quality_warnings_count: int
    resolved_warnings: List[str]
    hypotheses_shift: Dict[str, Any]
    remaining_uncertainty_kwh: float
    remaining_uncertainty_pct: float
    data_protection: DataProtectionGuaranteeSchema
    executed_at: str


class WhatIfCatalogItemSchema(BaseModel):
    scenario_type: str
    title: str
    category: str
    description: str
    typical_impact: str
    default_parameters: Dict[str, Any]

