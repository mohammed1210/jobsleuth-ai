"""Test Stripe webhook shape and plan mapping."""

import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from main import app

client = TestClient(app)


@patch("routes.stripe_webhook.stripe")
@patch("routes.stripe_webhook.supabase_admin")
def test_webhook_valid_signature(mock_supabase, mock_stripe):
    """Test webhook with valid signature returns {ok: true}."""
    # Mock stripe event construction
    mock_event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_123",
                "customer_email": "test@example.com",
                "line_items": None,
                "amount_total": 5000,
            }
        }
    }
    mock_stripe.Webhook.construct_event.return_value = mock_event
    
    # Mock supabase upsert
    mock_response = Mock()
    mock_response.data = []
    mock_query = Mock()
    mock_query.execute.return_value = mock_response
    mock_table = Mock()
    mock_table.upsert.return_value = mock_query
    mock_supabase.table.return_value = mock_table
    
    response = client.post(
        "/stripe/webhook",
        content=b'{"test": "data"}',
        headers={"stripe-signature": "valid_sig"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data == {"ok": True}


@patch("routes.stripe_webhook.stripe")
def test_webhook_invalid_signature(mock_stripe):
    """Test webhook with invalid signature returns {ok: false} with 400."""
    mock_stripe.Webhook.construct_event.side_effect = mock_stripe.error.SignatureVerificationError(
        "Invalid signature", "sig"
    )
    
    response = client.post(
        "/stripe/webhook",
        content=b'{"test": "data"}',
        headers={"stripe-signature": "invalid_sig"},
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["ok"] is False
    assert "error" in data


@patch("routes.stripe_webhook.stripe")
@patch("routes.stripe_webhook.supabase_admin")
@patch("routes.stripe_webhook.settings")
def test_webhook_plan_mapping_pro(mock_settings, mock_supabase, mock_stripe):
    """Test that PRICE_ID_PRO maps to 'pro' plan."""
    mock_settings.PRICE_ID_PRO = "price_pro_123"
    mock_settings.PRICE_ID_INVESTOR = "price_investor_456"
    
    # Mock stripe event with pro price
    mock_event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_123",
                "customer_email": "pro@example.com",
                "line_items": {
                    "data": [
                        {
                            "price": {
                                "id": "price_pro_123"
                            }
                        }
                    ]
                },
            }
        }
    }
    mock_stripe.Webhook.construct_event.return_value = mock_event
    
    # Capture upsert call
    upsert_data = None
    def capture_upsert(data, **kwargs):
        nonlocal upsert_data
        upsert_data = data
        mock_response = Mock()
        mock_response.data = []
        mock_query = Mock()
        mock_query.execute.return_value = mock_response
        return mock_query
    
    mock_table = Mock()
    mock_table.upsert.side_effect = capture_upsert
    mock_supabase.table.return_value = mock_table
    
    response = client.post(
        "/stripe/webhook",
        content=b'{"test": "data"}',
        headers={"stripe-signature": "valid_sig"},
    )
    
    assert response.status_code == 200
    assert upsert_data is not None
    assert upsert_data["plan"] == "pro"


@patch("routes.stripe_webhook.stripe")
@patch("routes.stripe_webhook.supabase_admin")
@patch("routes.stripe_webhook.settings")
def test_webhook_plan_mapping_investor(mock_settings, mock_supabase, mock_stripe):
    """Test that PRICE_ID_INVESTOR maps to 'investor' plan."""
    mock_settings.PRICE_ID_PRO = "price_pro_123"
    mock_settings.PRICE_ID_INVESTOR = "price_investor_456"
    
    # Mock stripe event with investor price
    mock_event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_456",
                "customer_email": "investor@example.com",
                "line_items": {
                    "data": [
                        {
                            "price": {
                                "id": "price_investor_456"
                            }
                        }
                    ]
                },
            }
        }
    }
    mock_stripe.Webhook.construct_event.return_value = mock_event
    
    # Capture upsert call
    upsert_data = None
    def capture_upsert(data, **kwargs):
        nonlocal upsert_data
        upsert_data = data
        mock_response = Mock()
        mock_response.data = []
        mock_query = Mock()
        mock_query.execute.return_value = mock_response
        return mock_query
    
    mock_table = Mock()
    mock_table.upsert.side_effect = capture_upsert
    mock_supabase.table.return_value = mock_table
    
    response = client.post(
        "/stripe/webhook",
        content=b'{"test": "data"}',
        headers={"stripe-signature": "valid_sig"},
    )
    
    assert response.status_code == 200
    assert upsert_data is not None
    assert upsert_data["plan"] == "investor"


@patch("routes.stripe_webhook.stripe")
def test_webhook_invalid_payload(mock_stripe):
    """Test webhook with invalid payload returns {ok: false} with 400."""
    mock_stripe.Webhook.construct_event.side_effect = ValueError("Invalid payload")
    
    response = client.post(
        "/stripe/webhook",
        content=b'invalid json',
        headers={"stripe-signature": "sig"},
    )
    
    assert response.status_code == 400
    data = response.json()
    assert data["ok"] is False
    assert "error" in data
