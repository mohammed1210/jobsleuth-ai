"""Synchronise verified Stripe events against canonical subscription state."""
from uuid import UUID
import stripe
from fastapi import APIRouter, HTTPException, Request
from lib.settings import settings
from lib.supabase import get_supabase_client

router = APIRouter(prefix="/stripe", tags=["billing"])
EVENT_TYPES = {"checkout.session.completed", "customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted", "invoice.paid", "invoice.payment_failed"}

def map_price_to_plan(price_id: str) -> str:
    mapping = {settings.NEXT_PUBLIC_STRIPE_PRICE_CAREER_PLUS: "career_plus", settings.NEXT_PUBLIC_STRIPE_PRICE_PRO: "pro"}
    return mapping.get(price_id, "free") if price_id.startswith("price_") else "free"

def _uuid(value):
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        return None

def _subscription_id(event):
    obj = event["data"]["object"]
    if event["type"] == "checkout.session.completed":
        return obj.get("subscription")
    if event["type"].startswith("customer.subscription."):
        return obj.get("id")
    parent = obj.get("parent") or {}
    return obj.get("subscription") or (parent.get("subscription_details") or {}).get("subscription")

def sync_subscription(subscription):
    user_id = _uuid((subscription.get("metadata") or {}).get("user_id"))
    if not user_id:
        raise ValueError("Missing verified subscription user mapping")
    customer = subscription.get("customer")
    subscription_id = subscription.get("id")
    if not customer or not subscription_id:
        raise ValueError("Missing subscription identifiers")
    table = get_supabase_client().table("subscriptions")
    result = table.select("*").eq("user_id", user_id).execute()
    existing = result.data or []
    if existing and existing[0].get("stripe_customer_id") not in (None, customer):
        raise ValueError("Customer ownership conflict")
    items = (subscription.get("items") or {}).get("data") or []
    price = ((items[0].get("price") or {}).get("id") if items else "") or ""
    status = subscription.get("status") or "inactive"
    plan = map_price_to_plan(price) if status in {"active", "trialing"} else "free"
    payload = {"user_id": user_id, "stripe_customer_id": customer, "stripe_subscription_id": subscription_id, "plan": plan, "status": status}
    if existing:
        table.update(payload).eq("user_id", user_id).execute()
    else:
        table.insert(payload).execute()

@router.post("/webhook")
async def stripe_webhook(request: Request):
    if not settings.STRIPE_WEBHOOK_SECRET or not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe webhooks not configured")
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(status_code=503, detail="Billing storage unavailable")
    try:
        event = stripe.Webhook.construct_event(await request.body(), request.headers.get("stripe-signature"), settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook signature") from exc
    event_type = event["type"]
    if event_type not in EVENT_TYPES:
        return {"ok": True, "event_type": event_type}
    subscription_id = _subscription_id(event)
    if not subscription_id:
        if event_type.startswith("invoice."):
            return {"ok": True, "event_type": event_type}
        raise HTTPException(status_code=422, detail="Missing subscription identifier")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        # Read current state so stale or duplicate deliveries cannot re-grant paid access.
        if event_type == "customer.subscription.deleted":
            # Cancelled subscriptions can be absent from Stripe's retrieve API;
            # deletion event payload is signature-verified and authoritative.
            snapshot = dict(event["data"]["object"])
            snapshot["status"] = "canceled"
        else:
            subscription = stripe.Subscription.retrieve(subscription_id)
            snapshot = subscription.to_dict_recursive() if hasattr(subscription, "to_dict_recursive") else dict(subscription)
        sync_subscription(snapshot)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Subscription synchronisation failed") from exc
    return {"ok": True, "event_type": event_type}
