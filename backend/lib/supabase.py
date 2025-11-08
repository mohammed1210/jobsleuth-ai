"""Supabase client initialization."""

from supabase import Client, create_client

from lib.settings import settings


def get_supabase_client() -> Client:
    """Get Supabase client with service role key."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_supabase_anon_client() -> Client:
    """Get Supabase client with anon key (for user operations)."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


# Singleton instances
supabase_admin = get_supabase_client()
supabase = get_supabase_anon_client()
