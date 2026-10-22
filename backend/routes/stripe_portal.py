"""Authenticated customer-owned Stripe billing portal."""
import stripe
from uuid import UUID
from fastapi import APIRouter, Header, HTTPException
from lib.settings import settings
from lib.supabase import get_supabase_client
from routes.saved_jobs import verify_supabase_user

router = APIRouter(prefix="/stripe", tags=["billing"])

@router.post("/create-portal-session")
async def create_portal_session(authorization: str | None = Header(None)) -> dict[str, str]:
    if not settings.STRIPE_SECRET_KEY or not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(status_code=503, detail="Billing is not configured")
    user = await verify_supabase_user(authorization)
    try:
        UUID(user["id"])
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(status_code=401, detail="A verified account is required") from exc
    result = get_supabase_client().table("subscriptions").select("stripe_customer_id").eq("user_id", user["id"]).execute()
    rows = result.data or []
    if not rows or not rows[0].get("stripe_customer_id"):
        raise HTTPException(status_code=404, detail="No billing account found")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        session = stripe.billing_portal.Session.create(
            customer=rows[0]["stripe_customer_id"],
            return_url=f"{settings.FRONTEND_URL.rstrip('/')}/account",
        )
    except stripe.StripeError as exc:
        raise HTTPException(status_code=502, detail="Billing portal is temporarily unavailable") from exc
    return {"url": session.url}
