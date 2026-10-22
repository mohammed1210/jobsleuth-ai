"""Authenticated subscription checkout for known JobSleuth plans."""
import stripe
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from lib.settings import settings
from lib.supabase import get_supabase_client
from routes.saved_jobs import verify_supabase_user

router = APIRouter(prefix="/stripe", tags=["billing"])

class CheckoutRequest(BaseModel):
    plan: str

def _allowed_prices() -> dict[str, str]:
    return {
        plan: price
        for plan, price in (
            ("career_plus", settings.NEXT_PUBLIC_STRIPE_PRICE_CAREER_PLUS),
            ("pro", settings.NEXT_PUBLIC_STRIPE_PRICE_PRO),
        )
        if price.startswith("price_") and not price.endswith("_xxx")
    }

def _billing_user(user: dict[str, str]) -> dict:
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(status_code=503, detail="Billing database is not configured")
    result = get_supabase_client().table("subscriptions").select("*").eq("user_id", user["id"]).execute()
    return (result.data or [{}])[0]

@router.post("/checkout")
async def create_checkout_session(request: CheckoutRequest, authorization: str | None = Header(None)) -> dict[str, str]:
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe is not configured")
    prices = _allowed_prices()
    if request.plan not in prices:
        raise HTTPException(status_code=422, detail="Unknown billing plan")
    if not settings.SUPABASE_URL:
        raise HTTPException(status_code=503, detail="Authentication is not configured")
    user = await verify_supabase_user(authorization)
    billing = _billing_user(user)
    stripe.api_key = settings.STRIPE_SECRET_KEY
    params = dict(
        mode="subscription",
        line_items=[{"price": prices[request.plan], "quantity": 1}],
        client_reference_id=user["id"],
        metadata={"user_id": user["id"], "plan": request.plan},
        subscription_data={"metadata": {"user_id": user["id"], "plan": request.plan}},
        success_url=f"{settings.FRONTEND_URL.rstrip('/')}/account?success=true&session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.FRONTEND_URL.rstrip('/')}/pricing?canceled=true",
    )
    if billing.get("stripe_customer_id"):
        params["customer"] = billing["stripe_customer_id"]
    elif user.get("email"):
        params["customer_email"] = user["email"]
    try:
        session = stripe.checkout.Session.create(**params)
    except stripe.StripeError as exc:
        raise HTTPException(status_code=502, detail="Checkout is temporarily unavailable") from exc
    return {"url": session.url}
