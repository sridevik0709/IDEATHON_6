-- ==============================================================================
-- GRIDGUARD NEXUS X - PostgreSQL Persistent Storage Initialization Script
-- Level 2: Data Foundation Schema Baseline
-- ==============================================================================

-- Create cryptographic & UUID extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

SET client_encoding = 'UTF8';
SET timezone = 'UTC';

-- Schema Migration Tracking
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(64) NOT NULL UNIQUE,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

INSERT INTO schema_migrations (version, description)
VALUES ('2.0.0-level2', 'Level 2: Data Foundation core schema')
ON CONFLICT (version) DO NOTHING;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    username VARCHAR(64) NOT NULL UNIQUE,
    email VARCHAR(128) NOT NULL UNIQUE,
    full_name VARCHAR(128) NOT NULL,
    hashed_password VARCHAR(256) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'GRID_ANALYST',
    permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 2. Data Sources Table
CREATE TABLE IF NOT EXISTS data_sources (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    code VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(128) NOT NULL,
    source_type VARCHAR(32) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_authorized BOOLEAN NOT NULL DEFAULT FALSE,
    configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_data_sources_code ON data_sources(code);
CREATE INDEX IF NOT EXISTS idx_data_sources_type ON data_sources(source_type);

-- 3. Network Assets Table
CREATE TABLE IF NOT EXISTS network_assets (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    asset_code VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(128) NOT NULL,
    asset_type VARCHAR(32) NOT NULL,
    voltage_class VARCHAR(32) NOT NULL,
    rated_capacity_kva DOUBLE PRECISION,
    status VARCHAR(32) NOT NULL DEFAULT 'OPERATIONAL',
    location_coordinates JSONB,
    is_simulated BOOLEAN NOT NULL DEFAULT TRUE,
    source_id VARCHAR(36) NOT NULL REFERENCES data_sources(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_network_assets_code ON network_assets(asset_code);
CREATE INDEX IF NOT EXISTS idx_network_assets_type ON network_assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_network_assets_sim ON network_assets(is_simulated);

-- 4. Network Relationships (Hierarchical Grid Topology)
CREATE TABLE IF NOT EXISTS network_relationships (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    parent_asset_id VARCHAR(36) NOT NULL REFERENCES network_assets(id) ON DELETE CASCADE,
    child_asset_id VARCHAR(36) NOT NULL REFERENCES network_assets(id) ON DELETE CASCADE,
    relationship_type VARCHAR(32) NOT NULL DEFAULT 'SUPPLIES',
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    valid_to TIMESTAMP WITH TIME ZONE,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    is_simulated BOOLEAN NOT NULL DEFAULT TRUE,
    notes VARCHAR(256),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_net_rel_parent ON network_relationships(parent_asset_id);
CREATE INDEX IF NOT EXISTS idx_net_rel_child ON network_relationships(child_asset_id);
CREATE INDEX IF NOT EXISTS idx_net_rel_current ON network_relationships(is_current);

-- 5. Household Aggregate Meters Table
CREATE TABLE IF NOT EXISTS household_aggregate_meters (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    meter_code VARCHAR(64) NOT NULL UNIQUE,
    household_count INTEGER NOT NULL DEFAULT 1,
    associated_asset_id VARCHAR(36) NOT NULL REFERENCES network_assets(id) ON DELETE CASCADE,
    installation_type VARCHAR(48) NOT NULL DEFAULT 'AGGREGATE_CONSUMER_CLUSTER',
    phase_configuration VARCHAR(24) NOT NULL DEFAULT 'THREE_PHASE',
    multiplier DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    is_simulated BOOLEAN NOT NULL DEFAULT TRUE,
    source_id VARCHAR(36) NOT NULL REFERENCES data_sources(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_hh_meters_code ON household_aggregate_meters(meter_code);
CREATE INDEX IF NOT EXISTS idx_hh_meters_asset ON household_aggregate_meters(associated_asset_id);

-- 6. Consumption Readings Table (Downstream Time-series)
CREATE TABLE IF NOT EXISTS consumption_readings (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    meter_id VARCHAR(36) NOT NULL REFERENCES household_aggregate_meters(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    energy_kwh DOUBLE PRECISION NOT NULL,
    reactive_energy_kvarh DOUBLE PRECISION,
    peak_power_kw DOUBLE PRECISION,
    interval_minutes INTEGER NOT NULL DEFAULT 60,
    unit VARCHAR(16) NOT NULL DEFAULT 'KWH',
    reading_type VARCHAR(32) NOT NULL DEFAULT 'INTERVAL',
    validation_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    is_simulated BOOLEAN NOT NULL DEFAULT TRUE,
    source_id VARCHAR(36) NOT NULL REFERENCES data_sources(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_meter_timestamp_reading_type UNIQUE (meter_id, timestamp, reading_type)
);
CREATE INDEX IF NOT EXISTS idx_consumption_meter_time ON consumption_readings(meter_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_consumption_val_status ON consumption_readings(validation_status);

-- 7. Distribution Boundary Energy Readings Table
CREATE TABLE IF NOT EXISTS distribution_boundary_readings (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    asset_id VARCHAR(36) NOT NULL REFERENCES network_assets(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    energy_kwh DOUBLE PRECISION NOT NULL,
    power_kw DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    voltage_v DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    current_a DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    power_factor DOUBLE PRECISION NOT NULL DEFAULT 0.95,
    frequency_hz DOUBLE PRECISION NOT NULL DEFAULT 50.0,
    unit VARCHAR(16) NOT NULL DEFAULT 'KWH',
    boundary_type VARCHAR(32) NOT NULL,
    validation_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    is_simulated BOOLEAN NOT NULL DEFAULT TRUE,
    source_id VARCHAR(36) NOT NULL REFERENCES data_sources(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_asset_time_boundary UNIQUE (asset_id, timestamp, boundary_type)
);
CREATE INDEX IF NOT EXISTS idx_boundary_asset_time ON distribution_boundary_readings(asset_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_boundary_val_status ON distribution_boundary_readings(validation_status);

-- 8. Data Quality Results Table
CREATE TABLE IF NOT EXISTS data_quality_results (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    target_type VARCHAR(32) NOT NULL,
    target_id VARCHAR(36) NOT NULL,
    quality_dimension VARCHAR(32) NOT NULL,
    passed BOOLEAN NOT NULL,
    score DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    error_code VARCHAR(64),
    diagnostic_message TEXT NOT NULL,
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_simulated BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_quality_target ON data_quality_results(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_quality_passed ON data_quality_results(passed);

-- 9. Anomaly Events Table
CREATE TABLE IF NOT EXISTS anomaly_events (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    event_code VARCHAR(64) NOT NULL UNIQUE,
    anomaly_type VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL DEFAULT 'MEDIUM',
    related_asset_id VARCHAR(36) REFERENCES network_assets(id) ON DELETE SET NULL,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    time_window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    time_window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    discrepancy_kwh DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    discrepancy_percent DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    status VARCHAR(32) NOT NULL DEFAULT 'DETECTED',
    description TEXT NOT NULL,
    is_simulated BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_anomaly_code ON anomaly_events(event_code);
CREATE INDEX IF NOT EXISTS idx_anomaly_type ON anomaly_events(anomaly_type);
CREATE INDEX IF NOT EXISTS idx_anomaly_severity ON anomaly_events(severity);

-- 10. Investigation Cases Table
CREATE TABLE IF NOT EXISTS investigation_cases (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    case_number VARCHAR(64) NOT NULL UNIQUE,
    title VARCHAR(128) NOT NULL,
    priority VARCHAR(16) NOT NULL DEFAULT 'MEDIUM',
    status VARCHAR(32) NOT NULL DEFAULT 'OPEN',
    primary_anomaly_id VARCHAR(36) REFERENCES anomaly_events(id) ON DELETE SET NULL,
    target_asset_id VARCHAR(36) REFERENCES network_assets(id) ON DELETE SET NULL,
    assigned_to_user_id VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    assigned_role VARCHAR(32) NOT NULL DEFAULT 'GRID_ANALYST',
    summary TEXT NOT NULL,
    is_simulated BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cases_number ON investigation_cases(case_number);
CREATE INDEX IF NOT EXISTS idx_cases_status ON investigation_cases(status);

-- 11. Evidence Records Table
CREATE TABLE IF NOT EXISTS evidence_records (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    case_id VARCHAR(36) NOT NULL REFERENCES investigation_cases(id) ON DELETE CASCADE,
    evidence_type VARCHAR(48) NOT NULL,
    title VARCHAR(128) NOT NULL,
    description TEXT NOT NULL,
    payload_data JSONB NOT NULL,
    hash_sha256 VARCHAR(64) NOT NULL,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    collected_by VARCHAR(64) NOT NULL,
    is_simulated BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_evidence_case ON evidence_records(case_id);

-- 12. Investigation Actions Table
CREATE TABLE IF NOT EXISTS investigation_actions (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    case_id VARCHAR(36) NOT NULL REFERENCES investigation_cases(id) ON DELETE CASCADE,
    action_type VARCHAR(48) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    performed_by VARCHAR(64) NOT NULL,
    notes TEXT NOT NULL,
    action_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    result_summary TEXT,
    is_simulated BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_actions_case ON investigation_actions(case_id);

-- 13. Investigation Outcomes Table
CREATE TABLE IF NOT EXISTS investigation_outcomes (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    case_id VARCHAR(36) NOT NULL UNIQUE REFERENCES investigation_cases(id) ON DELETE CASCADE,
    outcome_type VARCHAR(64) NOT NULL,
    estimated_loss_kwh DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    estimated_financial_loss_inr DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    action_taken TEXT NOT NULL,
    closed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    closed_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_outcomes_case ON investigation_outcomes(case_id);

-- 14. Scenario Runs Table
CREATE TABLE IF NOT EXISTS scenario_runs (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    scenario_code VARCHAR(32) NOT NULL,
    scenario_name VARCHAR(128) NOT NULL,
    seed INTEGER NOT NULL DEFAULT 42,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(32) NOT NULL DEFAULT 'RUNNING',
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    records_generated_count INTEGER NOT NULL DEFAULT 0,
    summary_metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_simulated BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scenario_runs_code ON scenario_runs(scenario_code);

-- 15. Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    actor_id VARCHAR(64) NOT NULL,
    actor_role VARCHAR(32) NOT NULL DEFAULT 'SYSTEM',
    action VARCHAR(64) NOT NULL,
    entity_type VARCHAR(64) NOT NULL,
    entity_id VARCHAR(64) NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);

-- Baseline Seed Data: Default Data Sources
INSERT INTO data_sources (id, code, name, source_type, is_active, is_authorized, configuration)
VALUES 
    ('00000000-0000-0000-0000-000000000001', 'SRC-SYNTHETIC-SIM-01', 'Synthetic Grid Demonstration Engine', 'SYNTHETIC', TRUE, TRUE, '{"interval_minutes": 60, "deterministic": true}'::jsonb),
    ('00000000-0000-0000-0000-000000000002', 'SRC-LOCAL-CSV-01', 'Local Test File Ingest Adapter', 'LOCAL_FILE', TRUE, TRUE, '{"supported_formats": ["csv", "json"]}'::jsonb),
    ('00000000-0000-0000-0000-000000000003', 'SRC-SCADA-UTILITY-01', 'Utility SCADA Telemetry Stream (Pending)', 'UTILITY_SCADA', FALSE, FALSE, '{"status": "PENDING_UTILITY_AUTHORIZATION"}'::jsonb)
ON CONFLICT (code) DO NOTHING;
