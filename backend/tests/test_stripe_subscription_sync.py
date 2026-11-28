from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from main import app
from lib.settings import settings
from routes import stripe_webhook

USER = "00000000-0000-4000-8000-000000000001"


def snapshot(status="active", sub="sub_test", created=100):
    return {
        "id": sub, "customer": "cus_test", "created": created,
        "metadata": {"user_id": USER}, "status": status,
        "items": {"data": [{"price": {"id": "price_pro_test"}}]},
    }


def fake_client(monkeypatch, revision=None, outcome="applied"):
    client = Mock()
    client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = (
        [] if revision is None else [{"billing_revision": revision}]
    )
    client.rpc.return_value.execute.return_value.data = outcome
    monkeypatch.setattr(stripe_webhook, "get_supabase_client", lambda: client)
    monkeypatch.setattr(settings, "NEXT_PUBLIC_STRIPE_PRICE_PRO", "price_pro_test")
    return client


def configure_webhook(monkeypatch):
    for name, value in {
        "STRIPE_WEBHOOK_SECRET": "whsec_test",
        "STRIPE_SECRET_KEY": "fake_test_key",
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "fake_service_key",
    }.items():
        monkeypatch.setattr(settings, name, value)


def send_event(monkeypatch, event_type, obj):
    monkeypatch.setattr(stripe_webhook.stripe.Webhook, "construct_event",
                        lambda *args: {"type": event_type, "data": {"object": obj}})
    return TestClient(app).post("/stripe/webhook", content=b"mock-signed-payload",
                                headers={"stripe-signature": "t=1,v1=mock"})


@pytest.mark.parametrize("status,plan", [
    ("active", "pro"), ("trialing", "pro"), ("past_due", "free"),
    ("unpaid", "free"), ("canceled", "free"), ("incomplete", "free"),
])
def test_subscription_status_maps_to_safe_plan(monkeypatch, status, plan):
    client = fake_client(monkeypatch, revision=7)
    stripe_webhook.sync_subscription(snapshot(status))
    args = client.rpc.call_args.args
    assert args[0] == "billing_sync_subscription"
    assert args[1]["p_plan"] == plan
    assert args[1]["p_expected_revision"] == 7
    assert args[1]["p_subscription_created"] == 100


def test_subscription_mapping_must_be_valid_user_uuid(monkeypatch):
    client = fake_client(monkeypatch)
    bad = snapshot()
    bad["metadata"]["user_id"] = "user_123"
    with pytest.raises(ValueError, match="user mapping"):
        stripe_webhook.sync_subscription(bad)
    client.rpc.assert_not_called()


def test_invalid_signature_is_rejected(monkeypatch):
    configure_webhook(monkeypatch)
    response = TestClient(app).post("/stripe/webhook", content=b"{}",
                                    headers={"stripe-signature": "invalid"})
    assert response.status_code == 400


def test_revision_is_read_before_canonical_refresh(monkeypatch):
    client = fake_client(monkeypatch, revision=5)
    def refresh(sub):
        client.table.return_value.select.return_value.eq.return_value.execute.assert_called_once()
        return snapshot("canceled")
    stripe_webhook.sync_subscription(snapshot(), refresh=refresh)
    assert client.rpc.call_args.args[1]["p_status"] == "canceled"
    assert client.rpc.call_args.args[1]["p_expected_revision"] == 5


def test_delayed_paid_event_uses_current_cancelled_state(monkeypatch):
    configure_webhook(monkeypatch)
    client = fake_client(monkeypatch, revision=2)
    fetch = Mock(side_effect=[snapshot(), snapshot("canceled")])
    monkeypatch.setattr(stripe_webhook, "_retrieve_subscription", fetch)
    response = send_event(monkeypatch, "invoice.paid", {"subscription": "sub_test"})
    assert response.status_code == 200
    assert fetch.call_count == 2
    assert client.rpc.call_args.args[1]["p_plan"] == "free"


def test_concurrent_write_requests_retry_not_success(monkeypatch):
    configure_webhook(monkeypatch)
    client = fake_client(monkeypatch, revision=2, outcome="retry")
    monkeypatch.setattr(stripe_webhook, "_retrieve_subscription", lambda _: snapshot())
    response = send_event(monkeypatch, "customer.subscription.updated", {"id": "sub_test"})
    assert response.status_code == 503
    client.rpc.assert_called_once()


def test_webhook_persistence_failure_is_retryable(monkeypatch):
    configure_webhook(monkeypatch)
    client = fake_client(monkeypatch)
    client.rpc.return_value.execute.side_effect = RuntimeError("db unavailable")
    monkeypatch.setattr(stripe_webhook, "_retrieve_subscription", lambda _: snapshot())
    assert send_event(monkeypatch, "customer.subscription.updated", {"id": "sub_test"}).status_code == 503


def test_old_cancellation_is_acknowledged_only_if_database_ignores_it(monkeypatch):
    configure_webhook(monkeypatch)
    client = fake_client(monkeypatch, revision=3, outcome="ignored")
    fetch = Mock()
    monkeypatch.setattr(stripe_webhook, "_retrieve_subscription", fetch)
    assert send_event(monkeypatch, "customer.subscription.deleted", snapshot()).status_code == 200
    fetch.assert_not_called()
    assert client.rpc.call_args.args[1]["p_status"] == "canceled"


def test_changed_owner_is_rejected_before_write(monkeypatch):
    client = fake_client(monkeypatch)
    changed = snapshot()
    changed["customer"] = "cus_other"
    with pytest.raises(ValueError, match="identity changed"):
        stripe_webhook.sync_subscription(snapshot(), refresh=lambda _: changed)
    client.rpc.assert_not_called()


def test_multiple_subscription_items_fail_closed(monkeypatch):
    client = fake_client(monkeypatch)
    mixed = snapshot()
    mixed["items"]["data"].append({"price": {"id": "price_unknown"}})
    stripe_webhook.sync_subscription(mixed)
    assert client.rpc.call_args.args[1]["p_plan"] == "free"


def test_installed_stripe_sdk_supports_retrieval_interface():
    # Real SDK construction: no HTTP request or actual credentials required.
    client = stripe_webhook.stripe.StripeClient("sk_test_synthetic_only")
    assert callable(client.v1.subscriptions.retrieve)


def test_retrieve_subscription_uses_instance_client(monkeypatch):
    retrieve = Mock(return_value=snapshot())
    client = Mock()
    client.v1.subscriptions.retrieve = retrieve
    factory = Mock(return_value=client)
    monkeypatch.setattr(stripe_webhook.stripe, "StripeClient", factory)
    assert stripe_webhook._retrieve_subscription("sub_test") == snapshot()
    factory.assert_called_once_with(settings.STRIPE_SECRET_KEY)
    retrieve.assert_called_once_with("sub_test")
