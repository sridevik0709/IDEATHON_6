-- ==============================================================================
-- GRIDGUARD NEXUS X - PostgreSQL Persistent Storage Initialization Script
-- Level 1: Foundation Schema & Extension Setup
-- ==============================================================================

-- Create extension for UUIDs and cryptographic hashing
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Set client encoding and timezone
SET client_encoding = 'UTF8';
SET timezone = 'UTC';

-- Schema Migration History Table
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(64) NOT NULL UNIQUE,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Record Level 1 Baseline
INSERT INTO schema_migrations (version, description)
VALUES ('1.0.0-level1', 'Level 1: Project Foundation schema baseline')
ON CONFLICT (version) DO NOTHING;

-- Subsystem Diagnostics Log Table (Persistent audit of gateway probes)
CREATE TABLE IF NOT EXISTS platform_diagnostics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(64) NOT NULL,
    subsystem VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    details JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_platform_diagnostics_subsystem 
    ON platform_diagnostics(subsystem);
CREATE INDEX IF NOT EXISTS idx_platform_diagnostics_recorded_at 
    ON platform_diagnostics(recorded_at DESC);

-- Reserved Table Schemas (Provisioned for Level 2 & Level 3 migrations)
-- Table definitions for smart meter nodes, feeder topologies, energy balances, and forensic records
COMMENT ON TABLE schema_migrations IS 'Tracks progressive milestone migrations for GridGuard Nexus X';
COMMENT ON TABLE platform_diagnostics IS 'System probe and storage diagnostics history';
