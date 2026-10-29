# GRIDGUARD NEXUS X — API SPECIFICATION v1
**Version**: 1.0.0-level1  
**Protocol**: HTTP/1.1 REST + JSON  
**Base URL**: `http://localhost:8000/api/v1`  

---

## Endpoints

### 1. Health Probe & Subsystem Diagnostics
- **Method**: `GET`
- **Path**: `/api/v1/health` (also accessible at root `/health`)
- **Description**: Probes platform health, uptime, persistent storage connection, and subsystem readiness.
- **Success Response (HTTP 200)**:
```json
{
  "status": "success",
  "data": {
    "status": "healthy",
    "project": "GRIDGUARD NEXUS X",
    "version": "1.0.0-level1",
    "stage": "LEVEL 1: PROJECT FOUNDATION",
    "environment": "development",
    "uptime_seconds": 124.5,
    "database": {
      "name": "PostgreSQL Persistent Storage",
      "status": "operational",
      "details": "Connected to POSTGRESQL persistent storage [Dialect: postgresql]",
      "ready": true
    },
    "subsystems": [
      {
        "name": "API & Routing Gateway",
        "status": "operational",
        "details": "FastAPI ASGI Gateway active and accepting requests",
        "ready": true
      },
      {
        "name": "Energy Accounting Service",
        "status": "standby",
        "details": "Phase: Level 2 - Feeder balancing, transmission loss reconciliation",
        "ready": false
      },
      {
        "name": "Telemetry & Grid Data Processing Engine",
        "status": "standby",
        "details": "Phase: Level 2 - Smart meter stream ingest",
        "ready": false
      },
      {
        "name": "AI Grid Intelligence & Forensic Auditor",
        "status": "standby",
        "details": "Phase: Level 3 - Non-technical loss detection",
        "ready": false
      }
    ]
  },
  "meta": {
    "version": "1.0.0-level1",
    "timestamp": "2026-10-29T15:25:00Z",
    "request_id": "c138fd97-6a56-4c45-9831-29e2f89f0da1"
  }
}
```

---

### 2. Platform Version & Capability Introspection
- **Method**: `GET`
- **Path**: `/api/v1/version`
- **Description**: Returns software version, active development level, and capability state.
- **Success Response (HTTP 200)**:
```json
{
  "status": "success",
  "data": {
    "project_name": "GRIDGUARD NEXUS X",
    "version": "1.0.0-level1",
    "stage": "LEVEL 1: PROJECT FOUNDATION",
    "api_prefix": "/api/v1",
    "supported_protocols": ["HTTP/1.1", "JSON REST", "WebSocket Ready"],
    "capabilities": {
      "foundation": "Active (Level 1 Foundation)",
      "request_validation": "Active (Pydantic v2)",
      "persistent_storage": "PostgreSQL (Configured / Fallback Ready)",
      "energy_accounting": "Reserved (Level 2 Milestone)",
      "telemetry_stream": "Reserved (Level 2 Milestone)",
      "ai_investigation": "Reserved (Level 3 Milestone)"
    }
  },
  "meta": {
    "version": "1.0.0-level1",
    "timestamp": "2026-10-29T15:25:00Z"
  }
}
```

---

### 3. Request Validation Probe
- **Method**: `POST`
- **Path**: `/api/v1/validate/telemetry-envelope`
- **Description**: Validates telemetry envelope against strict Pydantic rules.
- **Request Body (JSON)**:
```json
{
  "station_id": "SUB-NORTH-01",
  "grid_frequency_hz": 50.02,
  "voltage_rms": 11000.0,
  "feeder_count": 8
}
```
- **Validation Rules**:
  - `station_id`: String, length 3-32, regex `^[A-Z0-9_\-]+$`
  - `grid_frequency_hz`: Float, range `[45.0, 65.0]` Hz
  - `voltage_rms`: Float, range `[0.0, 500000.0]` V
  - `feeder_count`: Integer, range `[1, 128]`
- **Success Response (HTTP 200)**:
```json
{
  "status": "success",
  "data": {
    "valid": true,
    "received_station": "SUB-NORTH-01",
    "nominal_band": "50Hz Standard (e.g. India / Europe / UK)",
    "voltage_class": "Medium Voltage (MV Substation)"
  },
  "meta": {
    "version": "1.0.0-level1",
    "timestamp": "2026-10-29T15:25:00Z"
  }
}
```
- **Validation Failure Response (HTTP 422)**:
```json
{
  "status": "error",
  "error": {
    "code": "ERR_VALIDATION_FAILED",
    "message": "Validation failed: Input should be greater than or equal to 45 for field 'grid_frequency_hz'",
    "field": "grid_frequency_hz",
    "details": [
      {
        "field": "grid_frequency_hz",
        "message": "Input should be greater than or equal to 45",
        "type": "greater_than_equal"
      }
    ]
  },
  "meta": {
    "version": "1.0.0-level1",
    "timestamp": "2026-10-29T15:25:00Z"
  }
}
```

---

### 3. Level 5: Evidence Traceability Graph
- **Method**: `GET`
- **Path**: `/api/v1/investigation/graph/{boundary_asset_code}`
- **Description**: Generates an interactive directed acyclic graph connecting detected discrepancies through source measurements, data-quality findings, competing hypotheses, and recommended verification actions to confirmed outcomes.
- **Path Parameter**: `boundary_asset_code` (e.g., `TX-NORTH-01`, `TX-SOUTH-02`)
- **Success Response (HTTP 200)**:
```json
{
  "status": "success",
  "data": {
    "boundary_asset_code": "TX-NORTH-01",
    "boundary_asset_name": "Transformer North 01",
    "generated_at": "2026-10-30T00:40:00Z",
    "total_nodes": 14,
    "total_edges": 16,
    "nodes": [
      {
        "id": "DISC-TX-NORTH-01",
        "label": "Boundary Discrepancy (26.20 kWh)",
        "node_type": "DISCREPANCY",
        "visual_state": "CALCULATED_FINDING",
        "source_id": "DISC-TX-NORTH-01",
        "measurement_value": 26.2,
        "measurement_unit": "kWh",
        "data_status": "FLAGGED",
        "calculation_formula": "E_unaccounted = E_in - E_downstream - E_tech = 127.60 - 101.40 - 0.00 = 26.20 kWh (20.53%)",
        "verification_status": "PENDING_VERIFICATION",
        "reasoning_rule": "Deterministic Energy Balance Audit",
        "supporting_evidence": ["Input telemetry: 127.60 kWh", "Recorded downstream sum: 101.40 kWh"],
        "missing_evidence": ["Full 24h reading coverage for AGG-MTR-004"]
      }
    ],
    "edges": [
      {
        "id": "EDGE-1",
        "source": "DISC-TX-NORTH-01",
        "target": "SRC-IN-1",
        "relationship": "DERIVED_FROM",
        "label": "Inflow Telemetry"
      }
    ]
  }
}
```

---

### 4. Level 5: What-If Scenario Catalog
- **Method**: `GET`
- **Path**: `/api/v1/investigation/what-if/scenarios`
- **Description**: Returns the catalog of supported what-if simulation templates with expected impacts and required parameters.
- **Success Response (HTTP 200)**:
```json
{
  "status": "success",
  "data": {
    "total_scenarios": 5,
    "scenarios": [
      {
        "scenario_type": "DELAYED_READINGS_ARRIVED",
        "title": "A Delayed Reading Becomes Available",
        "description": "Simulates arrival of delayed downstream meter packets (e.g., AMI collector latency resolved).",
        "expected_impact": "Downstream recorded energy increases; unmetered discrepancy decreases toward zero.",
        "required_parameters": ["simulated_delayed_kwh", "meter_id"]
      }
    ]
  }
}
```

---

### 5. Level 5: What-If Simulation Sandbox
- **Method**: `POST`
- **Path**: `/api/v1/investigation/what-if/simulate`
- **Description**: Executes an isolated in-memory simulation against a boundary dossier without mutating underlying database measurements. Persists the run separately in `scenario_runs` and `audit_logs`.
- **Request Body**:
```json
{
  "boundary_asset_code": "TX-NORTH-01",
  "scenario_type": "DELAYED_READINGS_ARRIVED",
  "simulated_delayed_kwh": 26.2,
  "meter_id": "AGG-MTR-004",
  "notes": "Simulating delayed AMI batch ingestion for cluster meter 004"
}
```
- **Success Response (HTTP 200)**:
```json
{
  "status": "success",
  "data": {
    "boundary_asset_code": "DT-11KV-415V-101",
    "boundary_asset_name": "Distribution Transformer 101",
    "scenario_type": "DELAYED_READINGS_ARRIVED",
    "scenario_title": "A delayed reading becomes available",
    "assumption_description": "Hypothetical addition of 25.00 kWh delayed downstream consumption reading for meter AGG-MTR-DT101-C.",
    "original_accounting": {
      "input_energy_kwh": 97.8,
      "downstream_energy_kwh": 95.18,
      "technical_loss_kwh": 0.0,
      "unaccounted_energy_kwh": 2.62,
      "discrepancy_percentage": 2.68,
      "neutral_classification": "NORMAL_TECHNICAL_LOSS",
      "classification_reason": "Discrepancy within expected Class 0.5 sensor error margins."
    },
    "revised_accounting": {
      "input_energy_kwh": 97.8,
      "downstream_energy_kwh": 111.68,
      "technical_loss_kwh": 0.0,
      "unaccounted_energy_kwh": 0.0,
      "discrepancy_percentage": 0.0,
      "neutral_classification": "NORMAL_TECHNICAL_LOSS",
      "classification_reason": "Hypothetical readings fully accounted for discrepancy."
    },
    "differences": {
      "delta_unaccounted_kwh": -2.62,
      "delta_discrepancy_pct": -2.68,
      "delta_downstream_kwh": 16.5,
      "delta_technical_loss_kwh": 0.0,
      "classification_changed": false,
      "original_classification": "NORMAL_TECHNICAL_LOSS",
      "revised_classification": "NORMAL_TECHNICAL_LOSS",
      "discrepancy_resolved": true
    },
    "original_quality_warnings_count": 0,
    "revised_quality_warnings_count": 0,
    "resolved_warnings": [],
    "hypotheses_shift": {},
    "remaining_uncertainty_kwh": 0.0,
    "remaining_uncertainty_pct": 0.0,
    "data_protection": {
      "original_records_unmodified": true,
      "scenario_run_id": "ce8fad60-6885-4922-b0cd-459366eea263",
      "correction_provenance": "HYPOTHETICAL_SIMULATION",
      "real_case_auto_resolution_prevented": true,
      "audit_notice": "Forensic Integrity Guarantee: Original telemetry readings in distribution_boundary_readings and consumption_readings remain strictly unmodified. This what-if analysis was evaluated in an isolated in-memory simulation sandbox. Real-world operational cases cannot be closed without physical field verification."
    },
    "executed_at": "2026-10-30T01:08:20.123456Z"
  }
}
```

---

## Standard Error Codes

| Code | HTTP Status | Description |
| :--- | :--- | :--- |
| `ERR_VALIDATION_FAILED` | 422 | Pydantic input schema validation failure |
| `ERR_RESOURCE_NOT_FOUND` | 404 | Endpoint or database entity not found |
| `ERR_METHOD_NOT_ALLOWED` | 405 | HTTP verb unsupported on target route |
| `ERR_DATABASE_UNAVAILABLE`| 503 | Persistent storage handshake failure |
| `ERR_CONFIGURATION_ERROR` | 500 | Missing or invalid runtime configuration |
| `ERR_INTERNAL_SERVER_ERROR` | 500 | Unhandled runtime exception |
