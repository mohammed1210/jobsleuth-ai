from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from main import app
from lib.settings import settings
from routes import stripe_webhook

class FakeTable:
    def __init__(self):
        self.rows = {}
        self.payload = None
        self.user_id = None
    def select(self, *args): return self
    def eq(self, field, value):
        if field == "user_id": self.user_id = value
        return self
    def execute(self):
        if self.payload:
            self.rows[self.payload["user_id"]] = self.payload
            self.payload = None
            return SimpleNamespace(data=[])
        row = self.rows.get(self.user_id)
        return SimpleNamespace(data=[row] if row else [])
    def update(self, payload): self.payload = payload; return self
    def insert(self, payload): self.payload = payload; return self

def test_subscription_sync_never_grants_paid_access_for_failed_or_cancelled_status(monkeypatch):
    table = FakeTable()
    monkeypatch.setattr(stripe_webhook, "get_supabase_client", lambda: SimpleNamespace(table=lambda name: table))
    user = "00000000-0000-4000-8000-000000000001"
    subscription = {
        "id": "sub_test", "customer": "cus_test", "metadata": {"user_id": user},
        "items": {"data": [{"price": {"id": "price_test"}}]}, "status": "active",
    }
    monkeypatch.setattr(settings, "NEXT_PUBLIC_STRIPE_PRICE_PRO", "price_test")
    stripe_webhook.sync_subscription(subscription)
    assert table.rows[user]["plan"] == "pro"
    for status in ("past_due", "unpaid", "canceled", "incomplete"):
        stripe_webhook.sync_subscription({**subscription, "status": status})
        assert table.rows[user]["plan"] == "free"

def test_subscription_mapping_must_be_valid_user_uuid(monkeypatch):
    table = FakeTable()
    monkeypatch.setattr(stripe_webhook, "get_supabase_client", lambda: SimpleNamespace(table=lambda name: table))
    with pytest.raises(ValueError, match="user mapping"):
        stripe_webhook.sync_subscription({"id":"sub_test","customer":"cus_test","status":"active","metadata":{"user_id":"user_123"}})

def test_invalid_signature_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test")
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "service_test")
    response = TestClient(app).post("/stripe/webhook", data=b"{}", headers={"stripe-signature":"invalid"})
    assert response.status_code == 400
