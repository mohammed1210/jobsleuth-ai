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

def test_signed_webhook_uses_current_cancelled_state(monkeypatch):
    """A delayed paid event must not restore access to a cancelled subscription."""
    table = FakeTable()
    user = "00000000-0000-4000-8000-000000000001"
    monkeypatch.setattr(stripe_webhook, "get_supabase_client", lambda: SimpleNamespace(table=lambda name: table))
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test")
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "service_test")
    monkeypatch.setattr(settings, "NEXT_PUBLIC_STRIPE_PRICE_PRO", "price_pro_test")
    event = {"type": "invoice.paid", "data": {"object": {"subscription": "sub_test"}}}
    monkeypatch.setattr(stripe_webhook.stripe.Webhook, "construct_event", lambda *args: event)
    subscription = {
        "id": "sub_test", "customer": "cus_test", "status": "canceled",
        "metadata": {"user_id": user},
        "items": {"data": [{"price": {"id": "price_pro_test"}}]},
    }
    monkeypatch.setattr(
        stripe_webhook.stripe.Subscription,
        "retrieve",
        lambda sub_id: dict(subscription),
    )
    response = TestClient(app).post(
        "/stripe/webhook", content=b"mock-signed-payload",
        headers={"stripe-signature": "t=1,v1=mock"},
    )
    assert response.status_code == 200
    assert table.rows[user]["plan"] == "free"
    assert table.rows[user]["status"] == "canceled"


def test_webhook_persistence_failure_is_retryable(monkeypatch):
    """Stripe must receive a non-2xx when Supabase cannot store a change."""
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test")
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "service_test")
    event = {"type": "customer.subscription.updated", "data": {"object": {"id": "sub_test"}}}
    monkeypatch.setattr(stripe_webhook.stripe.Webhook, "construct_event", lambda *args: event)
    monkeypatch.setattr(stripe_webhook.stripe.Subscription, "retrieve", lambda sub_id: {
        "id":"sub_test", "customer":"cus_test", "status":"active",
        "metadata":{"user_id":"00000000-0000-4000-8000-000000000001"},
        "items":{"data":[{"price":{"id":"price_pro_test"}}]},
    })
    class BrokenTable:
        def select(self, *args): return self
        def eq(self, *args): return self
        def execute(self): raise RuntimeError("db temporarily unavailable")
    monkeypatch.setattr(stripe_webhook, "get_supabase_client", lambda: SimpleNamespace(table=lambda _: BrokenTable()))
    response = TestClient(app).post(
        "/stripe/webhook", content=b"mock-signed-payload",
        headers={"stripe-signature":"t=1,v1=mock"},
    )
    assert response.status_code == 503


def test_old_cancel_event_preserves_current_subscription(monkeypatch):
    table = FakeTable()
    uid = '00000000-0000-4000-8000-000000000001'
    table.rows[uid] = {'user_id': uid, 'stripe_customer_id': 'cus_example', 'stripe_subscription_id': 'sub_new', 'status': 'active', 'plan': 'pro'}
    monkeypatch.setattr(stripe_webhook, 'get_supabase_client', lambda: SimpleNamespace(table=lambda name: table))
    stripe_webhook.sync_subscription({'id': 'sub_old', 'customer': 'cus_example', 'status': 'canceled', 'metadata': {'user_id': uid}, 'items': {'data': []}})
    assert table.rows[uid]['stripe_subscription_id'] == 'sub_new'
    assert table.rows[uid]['plan'] == 'pro'
