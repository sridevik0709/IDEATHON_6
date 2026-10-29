"""
Unit and integration tests for platform health-check endpoints.
"""

def test_health_check_endpoint(client):
    """Test that /api/v1/health returns 200 and standard envelope format."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    payload = response.json()
    assert payload["status"] == "success"
    assert "data" in payload
    assert "meta" in payload
    
    data = payload["data"]
    assert data["project"] == "GRIDGUARD NEXUS X"
    assert "5.0.0" in data["version"]
    assert "LEVEL 5" in data["stage"]
    assert data["uptime_seconds"] >= 0
    assert "database" in data
    assert data["database"]["name"] == "PostgreSQL Persistent Storage"
    assert "subsystems" in data
    assert len(data["subsystems"]) >= 4


def test_top_level_health_redirect(client):
    """Test that top-level /health redirects or resolves cleanly."""
    response = client.get("/health", follow_redirects=True)
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
