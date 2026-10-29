"""
Pydantic Schemas for Level 4: AI-Assisted Investigation.
Provides robust models for:
- Evidence records & citations
- Multi-hypothesis investigation matrices
- 6-factor explainable prioritization reports
- AI Investigation Assistant queries, responses, and guardrail validations
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.accounting import QualityFindingSchema, ReconciliationResponse


class EvidenceItemSchema(BaseModel):
    evidence_id: str = Field(..., description="Unique evidence locator (e.g. EV-BND-001, EV-DQ-003)")
    source_type: str = Field(..., description="Type of evidence source: BOUNDARY_MEASUREMENT, CONSUMPTION_READING, QUALITY_AUDIT, TOPOLOGY_RELATIONSHIP")
    entity_code: str = Field(..., description="Target asset or meter code")
    timestamp_or_period: str = Field(..., description="Associated timestamp or time interval")
    metric_name: str = Field(..., description="Name of the quantified metric")
    metric_value: Any = Field(..., description="Concrete numerical or categorical value")
    unit: Optional[str] = Field(None, description="Physical unit of measurement (e.g. kWh, V, %)")
    description: str = Field(..., description="Detailed forensic context of the evidence item")


class HypothesisAnalysisSchema(BaseModel):
    hypothesis_id: str = Field(..., description="Unique identifier for the hypothesis docket")
    code: str = Field(..., description="Standard code (e.g., HYP_DELAYED_TELEMETRY, HYP_MAPPING_ERROR)")
    title: str = Field(..., description="Human-readable hypothesis title")
    category: str = Field(..., description="Domain category: TELEMETRY_LATENCY, DATA_QUALITY, TOPOLOGY_GIS, PHYSICS_TECHNICAL, COMMERCIAL_UNMETERED")
    explanation: str = Field(..., description="Comprehensive explanation of how this cause produces the observed discrepancy")
    plausibility: str = Field(..., description="HIGH, MEDIUM, LOW, or UNCONFIRMED")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Normalized score 0.0 to 1.0")
    confidence_rationale: str = Field(..., description="Explainable justification for the assigned confidence score")
    investigation_priority: str = Field(..., description="HIGH, MEDIUM, or LOW")
    investigation_status: str = Field(..., description="PLAUSIBLE, UNCONFIRMED, DISPROVEN, or RECOMMENDED_FOR_FIELD_CHECK")
    supporting_evidence: List[EvidenceItemSchema] = Field(default_factory=list, description="Verified concrete evidence items supporting this hypothesis")
    contradicting_evidence: List[EvidenceItemSchema] = Field(default_factory=list, description="Verified concrete evidence items contradicting this hypothesis")
    missing_evidence: List[str] = Field(default_factory=list, description="Missing telemetry or records needed to confirm/disprove")
    additional_data_required: List[str] = Field(default_factory=list, description="Actionable data sources or traces requested from utility")
    recommended_verification_steps: List[str] = Field(default_factory=list, description="Step-by-step physical or digital verification procedures")


class PrioritizationFactorSchema(BaseModel):
    factor_id: str = Field(..., description="Unique factor identifier")
    name: str = Field(..., description="Human-readable factor title")
    weight_percent: float = Field(..., description="Configured percentage weight (sum to 100%)")
    raw_value: Any = Field(..., description="Underlying unnormalized metric")
    normalized_score: float = Field(..., ge=0.0, le=100.0, description="Normalized scale (0.0 to 100.0)")
    weighted_contribution: float = Field(..., description="Points contributed: (weight / 100) * normalized_score")
    explanation: str = Field(..., description="Transparent rationale explaining the factor calculation")


class PrioritizationReportSchema(BaseModel):
    boundary_asset_code: str = Field(..., description="Analyzed boundary asset code")
    total_priority_score: float = Field(..., ge=0.0, le=100.0, description="Overall explainable priority index (0-100)")
    priority_level: str = Field(..., description="CRITICAL, HIGH, MEDIUM, or LOW")
    factors: List[PrioritizationFactorSchema] = Field(..., description="Itemized 6-factor mathematical contributions")
    top_recommended_hypothesis: str = Field(..., description="Primary hypothesis warranting first-line triage")
    operational_action_summary: str = Field(..., description="Executive recommendation for grid operations")


class InvestigationDossierResponse(BaseModel):
    boundary_asset_code: str
    boundary_asset_name: str
    voltage_class: str
    analysis_period_start: str
    analysis_period_end: str
    accounting: ReconciliationResponse
    hypotheses: List[HypothesisAnalysisSchema]
    prioritization: PrioritizationReportSchema
    generated_at: str


class AssistantQueryRequest(BaseModel):
    boundary_asset_code: str = Field(..., description="Target boundary asset code under investigation")
    query: str = Field(..., min_length=3, max_length=1000, description="User's investigation query")
    start_time: Optional[datetime] = Field(None, description="Optional start of measurement window")
    end_time: Optional[datetime] = Field(None, description="Optional end of measurement window")


class GuardrailValidationResultSchema(BaseModel):
    passed: bool = Field(..., description="True if response passed all deterministic safety guardrails")
    accounting_invariance_verified: bool = Field(..., description="True if no deterministic accounting results were altered")
    unsupported_allegations_prevented: bool = Field(..., description="True if unsupported accusations of theft/tampering were blocked or qualified")
    citations_verified: bool = Field(..., description="True if all cited entities, meters, and measurements exist in ground-truth dossier")
    hallucinated_utility_access_blocked: bool = Field(..., description="True if claims of unauthorized external utility database access were prevented")
    hypothetical_modifications_clearly_labeled: bool = Field(..., description="True if hypothetical corrections are clearly marked as non-real")
    rules_checked: List[str] = Field(default_factory=list, description="List of guardrail verification rules evaluated")
    validation_notes: List[str] = Field(default_factory=list, description="Specific safety findings from the validator")


class AssistantQueryResponse(BaseModel):
    boundary_asset_code: str
    query: str
    answer: str
    mode: str = Field(..., description="'RULE_BASED_FALLBACK' or 'EXTERNAL_AI'")
    model_name: str = Field(..., description="Underlying model identifier or 'Deterministic Evidence Synthesizer'")
    evidence_citations: List[EvidenceItemSchema] = Field(default_factory=list, description="Exact evidence items cited in the answer")
    suggested_followups: List[str] = Field(default_factory=list, description="Suggested follow-up investigation questions")
    guardrail_validation: GuardrailValidationResultSchema
    timestamp: str

