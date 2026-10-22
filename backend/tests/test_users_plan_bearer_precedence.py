"""Tests for users/plan endpoints with bearer token precedence."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_bearer_token_does_not_grant_mock_pro():
    """An arbitrary bearer string must never yield a Pro plan."""
    response = client.get("/users/me/plan", headers={"Authorization": "Bearer valid_token"})
    assert response.status_code in (401, 503)
    assert response.json().get("plan") != "pro"


def test_plan_requires_verified_subscription_storage():
    response = client.get("/users/me/plan", headers={"Authorization": "Bearer valid_token"})
    assert response.status_code in (401, 503)


def test_get_user_plan_without_token():
    """Test that missing token returns appropriate error."""
    response = client.get("/users/me/plan")
    assert response.status_code == 401
    
    data = response.json()
    assert "detail" in data
    assert "Bearer token" in data["detail"] or "Authorization" in data["detail"]


def test_invalid_token_format():
    """Test that invalid token format is rejected."""
    headers = {"Authorization": "InvalidFormat token"}
    response = client.get("/users/me/plan", headers=headers)
    assert response.status_code == 401


def test_get_user_profile():
    """Test retrieving user profile with bearer token."""
    headers = {"Authorization": "Bearer valid_token"}
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "user_id" in data
    assert "email" in data


def test_update_user_profile():
    """Test updating user profile with bearer token."""
    headers = {"Authorization": "Bearer valid_token"}
    profile_data = {"name": "Jane Doe"}
    response = client.put("/users/me", json=profile_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
