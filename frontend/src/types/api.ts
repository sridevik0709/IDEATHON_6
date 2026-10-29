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
