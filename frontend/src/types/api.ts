/**
 * API Type Definitions for GridGuard Nexus X
 * Mirrored from backend Pydantic models.
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
