"""Billing entrypoints must remain unavailable until securely configured."""
from fastapi.testclient import TestClient
from main import app
from lib.settings import settings

client = TestClient(app)

def test_checkout_disabled_by_default(monkeypatch):
    monkeypatch.setattr(settings, "BILLING_CHECKOUT_ENABLED", False)
    response = client.post("/stripe/checkout", json={"plan": "pro", "price_id": "price_attacker"})
    assert response.status_code == 503
    assert "not yet available" in response.json()["detail"]

def test_portal_rejects_unauthenticated_user():
    response = client.post("/stripe/create-portal-session", json={"customer_id": "cus_victim"})
    assert response.status_code in (401, 503)
    assert "url" not in response.json()
