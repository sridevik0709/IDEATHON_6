"""
Tests for consistent error responses, status codes, and Pydantic validation.
"""

def test_404_error_consistency(client):
    """Verify that an undefined route produces the standard error response envelope."""
    response = client.get("/api/v1/non-existent-endpoint")
    assert response.status_code == 404
    
    payload = response.json()
    assert payload["status"] == "error"
    assert "error" in payload
    assert "code" in payload["error"]
    assert payload["error"]["code"] == "ERR_RESOURCE_NOT_FOUND"
    assert "meta" in payload
    assert "timestamp" in payload["meta"]


def test_pydantic_validation_success(client):
    """Verify that valid input payload passes request validation."""
    valid_payload = {
        "station_id": "SUB-NORTH-01",
        "grid_frequency_hz": 50.02,
        "voltage_rms": 11000.0,
        "feeder_count": 8
    }
    response = client.post("/api/v1/validate/telemetry-envelope", json=valid_payload)
    assert response.status_code == 200
    
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["valid"] is True
    assert payload["data"]["received_station"] == "SUB-NORTH-01"
    assert "50Hz Standard" in payload["data"]["nominal_band"]


def test_pydantic_validation_failure_consistency(client):
    """Verify that invalid input produces 422 with standardized error envelope."""
    invalid_payload = {
        "station_id": "!@#$invalid_chars",  # fails regex pattern
        "grid_frequency_hz": 12.0,           # out of bounds (< 45)
        "voltage_rms": -50.0,                # negative voltage
        "feeder_count": 0                    # < 1
    }
    response = client.post("/api/v1/validate/telemetry-envelope", json=invalid_payload)
    assert response.status_code == 422
    
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error"]["code"] == "ERR_VALIDATION_FAILED"
    assert "details" in payload["error"]
    assert len(payload["error"]["details"]) > 0


def test_simulated_errors(client):
    """Verify that domain exceptions adhere to standard structure."""
    # 404 Domain exception
    res_404 = client.get("/api/v1/simulate-error?scenario=not_found")
    assert res_404.status_code == 404
    assert res_404.json()["error"]["code"] == "ERR_RESOURCE_NOT_FOUND"

    # 503 Database Unavailable
    res_503 = client.get("/api/v1/simulate-error?scenario=database")
    assert res_503.status_code == 503
    assert res_503.json()["error"]["code"] == "ERR_DATABASE_UNAVAILABLE"

    # 500 Configuration error
    res_500 = client.get("/api/v1/simulate-error?scenario=config")
    assert res_500.status_code == 500
    assert res_500.json()["error"]["code"] == "ERR_CONFIGURATION_ERROR"
