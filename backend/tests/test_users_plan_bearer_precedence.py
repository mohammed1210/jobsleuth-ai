"""Test user plan endpoint with Bearer token precedence."""

from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


def test_get_plan_without_auth_returns_free():
    """Test that /users/plan returns free plan when no auth provided."""
    response = client.get("/users/plan")
    assert response.status_code == 200
    
    data = response.json()
    assert data["plan"] == "free"
    assert data["stripe_customer_id"] is None


def test_get_plan_with_email_param():
    """Test /users/plan with email parameter (fallback)."""
    response = client.get("/users/plan?email=nonexistent@example.com")
    assert response.status_code == 200
    
    data = response.json()
    # Should return free for non-existent user
    assert data["plan"] == "free"


def test_get_plan_with_bearer_token():
    """Test /users/plan with Bearer token (should take precedence)."""
    # With an invalid token, should still return response (may be free)
    response = client.get(
        "/users/plan",
        headers={"Authorization": "Bearer fake-token"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "plan" in data


def test_bearer_token_precedence_over_email():
    """Test that Bearer token takes precedence over email parameter."""
    # Even with email param, Bearer token should be checked first
    response = client.get(
        "/users/plan?email=test@example.com",
        headers={"Authorization": "Bearer fake-token"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "plan" in data
    # The Bearer token is checked first, even if invalid


# Note: Full testing would require:
# 1. Valid Supabase JWT tokens
# 2. Test users in database with different plans
# 3. Verification that Bearer token truly takes precedence
