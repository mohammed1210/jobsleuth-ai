"""Tests for users/plan endpoints with bearer token precedence."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_bearer_token_takes_precedence():
    """Test that bearer token authentication takes precedence."""
    headers = {"Authorization": "Bearer valid_token"}
    response = client.get("/users/me/plan", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "user_id" in data
    assert "plan" in data


def test_get_user_plan_with_token():
    """Test retrieving user plan with bearer token."""
    headers = {"Authorization": "Bearer valid_token"}
    response = client.get("/users/me/plan", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "plan" in data
    assert "features" in data
    assert isinstance(data["features"], dict)


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
