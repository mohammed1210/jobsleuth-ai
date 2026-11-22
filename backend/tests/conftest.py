import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


import pytest
from fastapi import HTTPException


@pytest.fixture(autouse=True)
def synthetic_analysis_route_auth(monkeypatch):
    """Enable historical analysis fixtures with a TEST-ONLY fixed token.

    The actual verifier in routes.saved_jobs is NOT patched. New Stage 3
    verifier regression tests exercise it separately. No live credentials are
    ever loaded into the test suite; other bearer values remain unauthorized.
    """
    from routes import (
        application_builder,
        candidate_profile,
        evidence_bank,
        pilot_feedback,
        vacancy_analysis,
        vacancy_intelligence,
    )

    async def verified(authorization):
        if authorization != "Bearer valid_token":
            raise HTTPException(status_code=401, detail="Invalid synthetic test token")
        return {"id": "user_123", "email": "test@example.org"}

    for module in (
        application_builder,
        candidate_profile,
        evidence_bank,
        pilot_feedback,
        vacancy_analysis,
        vacancy_intelligence,
    ):
        monkeypatch.setattr(module, "verify_supabase_user", verified)
