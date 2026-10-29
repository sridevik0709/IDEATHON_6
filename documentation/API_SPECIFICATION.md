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

## Standard Error Codes

| Code | HTTP Status | Description |
| :--- | :--- | :--- |
| `ERR_VALIDATION_FAILED` | 422 | Pydantic input schema validation failure |
| `ERR_RESOURCE_NOT_FOUND` | 404 | Endpoint or database entity not found |
| `ERR_METHOD_NOT_ALLOWED` | 405 | HTTP verb unsupported on target route |
| `ERR_DATABASE_UNAVAILABLE`| 503 | Persistent storage handshake failure |
| `ERR_CONFIGURATION_ERROR` | 500 | Missing or invalid runtime configuration |
| `ERR_INTERNAL_SERVER_ERROR` | 500 | Unhandled runtime exception |
