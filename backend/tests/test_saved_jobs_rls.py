"""Tests for saved jobs with Row Level Security (owner-only access)."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_unauthenticated_cannot_save_jobs():
    """Test that unauthenticated users cannot save jobs."""
    response = client.post("/saved", json={"job_id": 1})
    assert response.status_code == 401
    
    data = response.json()
    assert "detail" in data


def test_unauthenticated_cannot_list_saved_jobs():
    """Test that unauthenticated users cannot list saved jobs."""
    response = client.get("/saved")
    assert response.status_code == 401


def test_user_can_save_job():
    """Test that authenticated user can save a job."""
    headers = {"Authorization": "Bearer valid_token"}
    response = client.post("/saved", json={"job_id": 1}, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "id" in data
    assert "user_id" in data
    assert data["job_id"] == 1


def test_user_can_view_own_saved_jobs():
    """Test that user can view their own saved jobs."""
    headers = {"Authorization": "Bearer valid_token"}
    response = client.get("/saved", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)


def test_invalid_token_rejected():
    """Test that invalid tokens are rejected."""
    headers = {"Authorization": "Bearer invalid"}
    response = client.get("/saved", headers=headers)
    assert response.status_code == 401


def test_missing_bearer_prefix():
    """Test that missing 'Bearer' prefix is rejected."""
    headers = {"Authorization": "valid_token"}
    response = client.get("/saved", headers=headers)
    assert response.status_code == 401
