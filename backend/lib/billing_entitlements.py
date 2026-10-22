"""Read-only, server-verified billing entitlements.

No mocked identities and no optimistic Pro access while billing storage is down.
"""
from uuid import UUID

from fastapi import HTTPException

from lib.settings import settings
from lib.supabase import get_supabase_client
from routes.saved_jobs import verify_supabase_user, _extract_token

PLANS = ("free", "career_plus", "pro")
ACTIVE_STATUSES = {"active", "trialing"}
FEATURES = {
    "free": {"paid_application_support": False, "advanced_application_support": False},
    "career_plus": {"paid_application_support": True, "advanced_application_support": False},
    "pro": {"paid_application_support": True, "advanced_application_support": True},
}


def resolve_plan(record: dict | None) -> str:
    if not record or record.get("status") not in ACTIVE_STATUSES:
        return "free"
    plan = record.get("plan")
    return plan if plan in ("career_plus", "pro") else "free"


async def get_entitlements(authorization: str | None) -> dict:
    _extract_token(authorization)
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(status_code=503, detail="Subscription verification unavailable")
    user = await verify_supabase_user(authorization)
    try:
        user_id = str(UUID(user["id"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Verified account required") from exc
    try:
        rows = (
            get_supabase_client()
            .table("subscriptions")
            .select("plan,status")
            .eq("user_id", user_id)
            .execute()
            .data or []
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Subscription verification unavailable") from exc
    plan = resolve_plan(rows[0] if rows else None)
    return {"user_id": user_id, "email": user.get("email", ""), "plan": plan, "features": FEATURES[plan]}
