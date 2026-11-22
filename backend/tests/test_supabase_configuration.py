"""Unconfigured Supabase never returns success-shaped placeholder clients."""
import pytest
from fastapi import HTTPException
from lib.settings import settings
from lib import supabase as lib


def test_admin_client_requires_real_service_role_configuration(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_URL", "")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")
    with pytest.raises(HTTPException) as raised:
        lib.get_supabase_client()
    assert raised.value.status_code == 503


def test_public_client_requires_real_anon_key(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_URL", "")
    monkeypatch.setattr(settings, "SUPABASE_KEY", "")
    with pytest.raises(HTTPException) as raised:
        lib.get_supabase_anon_client()
    assert raised.value.status_code == 503


def test_legacy_aliases_fail_closed_without_configuration(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_URL", "")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")
    monkeypatch.setattr(settings, "SUPABASE_KEY", "")
    for alias in (lib.supabase_admin, lib.supabase):
        with pytest.raises(HTTPException) as raised:
            alias.table("jobs")
        assert raised.value.status_code == 503
