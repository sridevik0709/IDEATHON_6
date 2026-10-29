/**
 * API Type Definitions for GridGuard Nexus X
 * Level 2: Data Foundation.
 */

export interface ResponseMeta {
  version: string;
  timestamp: string;
  request_id?: string | null;
}

export interface ErrorDetail {
  code: string;
  message: string;
  field?: string | null;
  details?: unknown;
}

export interface StandardSuccessResponse<T> {
  status: 'success';
  data: T;
  meta: ResponseMeta;
}

export interface StandardErrorResponse {
  status: 'error';
  error: ErrorDetail;
  meta: ResponseMeta;
}

export type ApiResponse<T> = StandardSuccessResponse<T> | StandardErrorResponse;

export interface SubsystemHealth {
  name: string;
  status: 'operational' | 'standby' | 'degraded' | 'disconnected' | string;
  details?: string | null;
  ready: boolean;
}

export interface HealthStatusData {
  status: string;
  project: string;
  version: string;
  stage: string;
  environment: string;
  uptime_seconds: number;
  database: SubsystemHealth;
  subsystems: SubsystemHealth[];
}

export interface VersionInfoData {
  project_name: string;
  version: string;
  stage: string;
  api_prefix: string;
  supported_protocols: string[];
  capabilities: Record<string, string>;
}

export interface ValidationProbeRequest {
  station_id: string;
  grid_frequency_hz: number;
  voltage_rms: number;
  feeder_count: number;
}

export interface ValidationProbeResponse {
  valid: boolean;
  received_station: string;
  nominal_band: string;
  voltage_class: string;
}

// -----------------------------------------------------------------------------
// Level 2: Data Foundation & Scenario Types
// -----------------------------------------------------------------------------
export interface ScenarioDescriptor {
  scenario_code: string;
  scenario_name: string;
  description: string;
  documented_inputs: Record<string, unknown>;
  expected_outcomes: Record<string, unknown>;
}

export interface ScenarioExecutionRequest {
  scenario_code: string;
  seed?: number;
  persist_to_database?: boolean;
}

export interface ScenarioExecutionResponse {
  scenario_code: string;
  scenario_name: string;
  seed: number;
  status: string;
  records_generated_count: number;
  summary_metrics: Record<string, unknown>;
  anomaly_count: number;
  cases_generated_count: number;
  run_id?: string | null;
  executed_at: string;
}

export interface DataSourceItem {
  id?: string;
  code: string;
  name: string;
  source_type: string;
  is_active: boolean;
  is_authorized: boolean;
  configuration?: Record<string, unknown>;
  message?: string;
}

export interface NetworkAssetItem {
  id: string;
  asset_code: string;
  name: string;
  asset_type: string;
  voltage_class: string;
  rated_capacity_kva?: number | null;
  status: string;
  location_coordinates?: Record<string, unknown> | null;
  is_simulated: boolean;
}

export interface InvestigationCaseItem {
  id: string;
  case_number: string;
  title: string;
  priority: string;
  status: string;
  summary: string;
  assigned_role: string;
  evidence_count: number;
  evidence: Array<{
    id: string;
    evidence_type: string;
    title: string;
    hash_sha256: string;
    collected_by: string;
    collected_at: string;
  }>;
  outcome?: {
    outcome_type: string;
    estimated_loss_kwh: number;
    estimated_financial_loss_inr: number;
    action_taken: string;
  } | null;
  is_simulated: boolean;
  created_at: string;
}

// ============================================================================
// LEVEL 3: CORE ELECTRICITY INTELLIGENCE TYPES
// ============================================================================

export interface QualityFindingData {
  rule_code: string;
  dimension: string;
  severity: string;
  passed: boolean;
  diagnostic_message: string;
  target_entity: string;
  details?: Record<string, unknown> | null;
  recommended_action?: string | null;
}

export interface MeterLookupData {
  meter_id: string;
  meter_code: string;
  household_count: number;
  associated_asset_id?: string | null;
  associated_asset_code?: string | null;
  associated_asset_name?: string | null;
  associated_asset_type?: string | null;
  installation_type: string;
  phase_configuration: string;
  multiplier: number;
  data_source_code: string;
  data_source_type: string;
  data_source_authorized: boolean;
  is_simulated: boolean;
  disclaimer: string;
}

export interface ConsumptionTrendPoint {
  timestamp: string;
  energy_kwh: number;
  peak_power_kw?: number | null;
  is_unusual: boolean;
  unusual_reason?: string | null;
}

export interface MeterConsumptionData {
  meter_code: string;
  household_count: number;
  analysis_period_start: string;
  analysis_period_end: string;
  total_consumption_kwh: number;
  average_hourly_kwh: number;
  peak_power_kw: number;
  minimum_interval_kwh: number;
  maximum_interval_kwh: number;
  readings_count: number;
  expected_readings_count: number;
  missing_intervals_count: number;
  missing_timestamps: string[];
  unusual_changes_count: number;
  data_quality_warnings: QualityFindingData[];
  trend_series: ConsumptionTrendPoint[];
  compliance_notice: string;
}

export interface CalculationStepData {
  step_number: number;
  title: string;
  formula: string;
  inputs: Record<string, unknown>;
  output_name: string;
  output_value: number;
  unit: string;
  explanation: string;
}

export interface SourceMeasurementTraceData {
  entity_code: string;
  entity_type: string;
  readings_count: number;
  total_energy_kwh: number;
  unit: string;
  interval_minutes: number;
  validation_status: string;
  data_source: string;
  is_simulated: boolean;
}

export interface AccountingBoundaryData {
  asset_code: string;
  name: string;
  asset_type: string;
  voltage_class: string;
  rated_capacity_kva: number;
  child_entities_count: number;
  child_type: string;
  status: string;
}

export interface AccountingDossierData {
  boundary_asset_code: string;
  boundary_asset_name: string;
  boundary_asset_type: string;
  voltage_class: string;
  time_window_start: string;
  time_window_end: string;
  total_expected_intervals: number;
  total_actual_intervals: number;
  missing_intervals_count: number;
  energy_entering_boundary_kwh: number;
  recorded_downstream_energy_kwh: number;
  other_accounted_flows_kwh: number;
  gross_discrepancy_kwh: number;
  unaccounted_energy_kwh: number;
  discrepancy_percentage: number;
  sensor_uncertainty_kwh: number;
  remaining_uncertainty_percent: number;
  neutral_classification: string;
  classification_reason: string;
  calculation_steps: CalculationStepData[];
  source_measurements: SourceMeasurementTraceData[];
  data_quality_findings: QualityFindingData[];
  reproducibility_hash: string;
}
