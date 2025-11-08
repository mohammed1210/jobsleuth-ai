"""Supabase client initialization."""


from lib.settings import settings
from supabase import Client, create_client

_supabase_admin: Client | None = None
_supabase: Client | None = None


def get_supabase_client() -> Client:
    """Get Supabase client with service role key (lazy initialization)."""
    global _supabase_admin
    if _supabase_admin is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            # Return a dummy client for testing/development
            # In production, this should raise an error
            class DummyClient:
                def table(self, name):
                    return self

                def select(self, *args, **kwargs):
                    return self

                def insert(self, *args, **kwargs):
                    return self

                def upsert(self, *args, **kwargs):
                    return self

                def update(self, *args, **kwargs):
                    return self

                def delete(self, *args, **kwargs):
                    return self

                def eq(self, *args, **kwargs):
                    return self

                def execute(self):
                    class Result:
                        data = []
                        count = 0

                    return Result()

            _supabase_admin = DummyClient()
        else:
            _supabase_admin = create_client(
                settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY
            )
    return _supabase_admin


def get_supabase_anon_client() -> Client:
    """Get Supabase client with anon key (for user operations)."""
    global _supabase
    if _supabase is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            # Return a dummy client for testing/development
            class DummyClient:
                def table(self, name):
                    return self

                class Auth:  # noqa: N801
                    @staticmethod
                    def get_user(token):
                        return None

                auth = Auth()

            _supabase = DummyClient()
        else:
            _supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _supabase


# Lazy-loaded instances
supabase_admin = get_supabase_client()
supabase = get_supabase_anon_client()
