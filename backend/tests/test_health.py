"""Test health endpoint."""

from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


def test_health_endpoint():
    """Test that health endpoint returns ok=True."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("ok") == True


def test_root_endpoint():
    """Test that root endpoint returns API info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["status"] == "operational"
