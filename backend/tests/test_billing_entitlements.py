"""The plan endpoint never trusts bearer text or returns mocked Pro access."""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from main import app
from lib.settings import settings
from lib import billing_entitlements as billing

def test_plan_resolution_denies_unpaid_states():
    for status in ("canceled", "past_due", "incomplete", "unpaid", None):
        assert billing.resolve_plan({"status": status, "plan": "pro"}) == "free"
    assert billing.resolve_plan({"status": "active", "plan": "pro"}) == "pro"
    assert billing.resolve_plan({"status": "trialing", "plan": "career_plus"}) == "career_plus"
    assert billing.resolve_plan({"status": "active", "plan": "investor"}) == "free"

def test_plan_endpoint_requires_billing_storage(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_URL", "")
    assert TestClient(app).get("/users/me/plan", headers={"Authorization":"Bearer anything"}).status_code == 503

@pytest.mark.asyncio
async def test_verified_user_without_subscription_is_free(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "service_role_test")
    async def verified(_authorization):
        return {"id":"00000000-0000-4000-8000-000000000001", "email":"test@example.com"}
    class Query:
        def select(self,*args): return self
        def eq(self,*args): return self
        def order(self,*args,**kwargs): return self
        def execute(self): return SimpleNamespace(data=[])
    monkeypatch.setattr(billing, "verify_supabase_user", verified)
    monkeypatch.setattr(billing, "get_supabase_client", lambda:SimpleNamespace(table=lambda _:Query()))
    result=await billing.get_entitlements("Bearer valid")
    assert result["plan"] == "free"
    assert not result["features"]["advanced_application_support"]

@pytest.mark.asyncio
async def test_billing_storage_error_never_defaults_to_pro(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "service_role_test")
    async def verified(_authorization):
        return {"id":"00000000-0000-4000-8000-000000000001"}
    class Query:
        def select(self,*args): return self
        def eq(self,*args): return self
        def execute(self): raise RuntimeError("db down")
    monkeypatch.setattr(billing, "verify_supabase_user", verified)
    monkeypatch.setattr(billing, "get_supabase_client",lambda:SimpleNamespace(table=lambda _:Query()))
    with pytest.raises(HTTPException) as error:
        await billing.get_entitlements("Bearer valid")
    assert error.value.status_code == 503

@pytest.mark.asyncio
async def test_latest_subscription_selected_when_old_canceled_row_exists(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "service_role_test")
    async def verified(_authorization):
        return {"id":"00000000-0000-4000-8000-000000000001", "email":"test@example.com"}
    class Query:
        def __init__(self):
            self.ordered = False
        def select(self,*args): return self
        def eq(self,*args): return self
        def order(self, column, desc=False):
            assert column == "updated_at"
            assert desc is True
            self.ordered = True
            return self
        def execute(self):
            assert self.ordered
            return SimpleNamespace(data=[
                {"plan":"pro", "status":"active"},
                {"plan":"free", "status":"canceled"},
            ])
    monkeypatch.setattr(billing, "verify_supabase_user", verified)
    monkeypatch.setattr(billing, "get_supabase_client", lambda:SimpleNamespace(table=lambda _:Query()))
    with pytest.raises(HTTPException) as error:
        await billing.get_entitlements("Bearer valid")
    assert error.value.status_code == 503
    assert "reconciliation" in error.value.detail
