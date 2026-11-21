"""Service-role and public Supabase clients, with no dummy production writes."""
from __future__ import annotations

from typing import Any, Callable

from fastapi import HTTPException
from lib.settings import settings
from supabase import Client, create_client

_supabase_admin: Client | None = None
_supabase: Client | None = None


def get_supabase_client() -> Client:
    """Use only a configured service-role client; never fabricate DB success."""
    global _supabase_admin
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(status_code=503, detail="Database service is not configured")
    if _supabase_admin is None:
        _supabase_admin = create_client(
            settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY
        )
    return _supabase_admin


def get_supabase_anon_client() -> Client:
    """Create the public-key client for user operations, or fail closed."""
    global _supabase
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise HTTPException(status_code=503, detail="Authentication service is not configured")
    if _supabase is None:
        _supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _supabase


class _LazyClient:
    """Legacy aliases for unused routes; no connection or dummy at import time."""
    def __init__(self, resolver: Callable[[], Client]) -> None:
        self.resolver = resolver

    def __getattr__(self, attr: str) -> Any:
        return getattr(self.resolver(), attr)


supabase_admin = _LazyClient(get_supabase_client)
supabase = _LazyClient(get_supabase_anon_client)
