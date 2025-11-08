"""Tests for health check endpoint."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


def test_health_check():
    """Test health check endpoint returns ok status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_check_always_available():
    """Test that health check is always available."""
    # Make multiple requests to ensure it's stable
    for _ in range(5):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
