"""
Unit tests for API version and platform introspection.
"""

def test_version_endpoint(client):
    """Test that /api/v1/version returns version information in standard envelope."""
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    
    payload = response.json()
    assert payload["status"] == "success"
    
    data = payload["data"]
    assert data["project_name"] == "GRIDGUARD NEXUS X"
    assert data["version"] == "1.0.0-level1"
    assert data["stage"] == "LEVEL 1: PROJECT FOUNDATION"
    assert data["api_prefix"] == "/api/v1"
    assert "capabilities" in data
    assert "foundation" in data["capabilities"]
