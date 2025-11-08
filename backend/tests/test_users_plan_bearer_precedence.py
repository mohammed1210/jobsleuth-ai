"""Test user plan endpoint with Bearer token precedence."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from main import app

client = TestClient(app)


@patch("routes.users.supabase")
@patch("routes.users.supabase_admin")
def test_get_plan_with_bearer_token(mock_admin, mock_supabase):
    """Test that Bearer token takes precedence over email parameter."""
    # Mock auth response
    mock_user = Mock()
    mock_user.email = "bearer@example.com"
    mock_user.id = "user-id-1"
    
    mock_auth_response = Mock()
    mock_auth_response.user = mock_user
    
    mock_supabase.auth.get_user.return_value = mock_auth_response
    
    # Mock user data response
    mock_response = Mock()
    mock_response.data = [
        {
            "email": "bearer@example.com",
            "plan": "pro",
            "stripe_customer_id": "cus_123",
        }
    ]
    
    mock_query = Mock()
    mock_query.execute.return_value = mock_response
    mock_query.eq.return_value = mock_query
    
    mock_table = Mock()
    mock_table.select.return_value = mock_query
    mock_admin.table.return_value = mock_table
    
    # Request with both Bearer token AND email param
    # Bearer should take precedence
    response = client.get(
        "/users/plan?email=other@example.com",
        headers={"Authorization": "Bearer test-token"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["plan"] == "pro"
    # Should have used Bearer token, not email param
    mock_supabase.auth.get_user.assert_called_once_with("test-token")


@patch("routes.users.supabase_admin")
def test_get_plan_with_email_fallback(mock_admin):
    """Test email parameter fallback when no Bearer token."""
    # Mock user data response
    mock_response = Mock()
    mock_response.data = [
        {
            "email": "email@example.com",
            "plan": "investor",
            "stripe_customer_id": "cus_456",
        }
    ]
    
    mock_query = Mock()
    mock_query.execute.return_value = mock_response
    mock_query.eq.return_value = mock_query
    
    mock_table = Mock()
    mock_table.select.return_value = mock_query
    mock_admin.table.return_value = mock_table
    
    response = client.get("/users/plan?email=email@example.com")
    
    assert response.status_code == 200
    data = response.json()
    assert data["plan"] == "investor"


@patch("routes.users.supabase_admin")
def test_get_plan_defaults_to_free(mock_admin):
    """Test that missing user defaults to free plan."""
    # Mock empty response
    mock_response = Mock()
    mock_response.data = []
    
    mock_query = Mock()
    mock_query.execute.return_value = mock_response
    mock_query.eq.return_value = mock_query
    
    mock_table = Mock()
    mock_table.select.return_value = mock_query
    mock_admin.table.return_value = mock_table
    
    response = client.get("/users/plan?email=nonexistent@example.com")
    
    assert response.status_code == 200
    data = response.json()
    assert data["plan"] == "free"
    assert data["stripe_customer_id"] is None
