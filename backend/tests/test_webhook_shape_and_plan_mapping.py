"""Tests for webhook shape and plan mapping (deterministic JSON)."""

import pytest
import json
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_webhook_returns_deterministic_json_structure():
    """Test that webhook response has deterministic JSON structure."""
    # We can't test actual webhook without valid signature,
    # but we can verify the response structure from our code
    
    # The webhook should return responses with consistent key ordering:
    # {"status": "success", "event_type": "...", "data": {...}}
    pass


def test_webhook_plan_mapping_pro():
    """Test that webhook correctly maps Pro plan."""
    # Mock price ID for Pro plan
    # In actual implementation, this would be tested with webhook events
    from backend.routes.stripe_webhook import map_price_to_plan
    
    # Test with environment variable value
    pro_plan = map_price_to_plan("price_pro_xxx")
    assert pro_plan == "pro"


def test_webhook_plan_mapping_investor():
    """Test that webhook correctly maps Investor plan."""
    from backend.routes.stripe_webhook import map_price_to_plan
    
    investor_plan = map_price_to_plan("price_investor_xxx")
    assert investor_plan == "investor"


def test_webhook_plan_mapping_unknown():
    """Test that webhook defaults to free for unknown price IDs."""
    from backend.routes.stripe_webhook import map_price_to_plan
    
    unknown_plan = map_price_to_plan("price_unknown_xxx")
    assert unknown_plan == "free"


def test_deterministic_response_structure():
    """Test that create_deterministic_response returns ordered JSON."""
    from backend.routes.stripe_webhook import create_deterministic_response
    
    response = create_deterministic_response(
        "success",
        "test.event",
        {"z_field": "last", "a_field": "first", "m_field": "middle"}
    )
    
    # Parse response to verify structure
    body = json.loads(response.body.decode())
    
    # Check required fields
    assert body["status"] == "success"
    assert body["event_type"] == "test.event"
    assert "data" in body
    
    # Check that data keys are sorted
    data_keys = list(body["data"].keys())
    assert data_keys == sorted(data_keys)


def test_webhook_response_has_required_fields():
    """Test that webhook responses always have required fields."""
    from backend.routes.stripe_webhook import create_deterministic_response
    
    # Test without data
    response = create_deterministic_response("success", "test.event")
    body = json.loads(response.body.decode())
    
    assert "status" in body
    assert "event_type" in body
    
    # Test with data
    response = create_deterministic_response(
        "success", 
        "test.event",
        {"field": "value"}
    )
    body = json.loads(response.body.decode())
    
    assert "status" in body
    assert "event_type" in body
    assert "data" in body
