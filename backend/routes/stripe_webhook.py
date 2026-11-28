"""Synchronise verified Stripe events against canonical subscription state."""
from uuid import UUID
import stripe
from fastapi import APIRouter, HTTPException, Request
from lib.settings import settings
from lib.supabase import get_supabase_client

router = APIRouter(prefix="/stripe", tags=["billing"])
EVENT_TYPES = {"checkout.session.completed", "customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted", "invoice.paid", "invoice.payment_failed"}

def map_price_to_plan(price_id: str) -> str:
    # Match the checkout allowlist: placeholders and ambiguous configuration
    # must never grant premium entitlements.
    if not isinstance(price_id, str) or not price_id.startswith("price_") or price_id.endswith("_xxx"):
        return "free"
    matches = [
        plan
        for plan, configured_price in (
            ("career_plus", settings.NEXT_PUBLIC_STRIPE_PRICE_CAREER_PLUS),
            ("pro", settings.NEXT_PUBLIC_STRIPE_PRICE_PRO),
        )
        if configured_price == price_id
    ]
    return matches[0] if len(matches) == 1 else "free"

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

def _identity(subscription):
    user_id = _uuid((subscription.get("metadata") or {}).get("user_id"))
    if not user_id:
        raise ValueError("Missing verified subscription user mapping")
    customer = subscription.get("customer")
    subscription_id = subscription.get("id")
    created = subscription.get("created")
    if not isinstance(customer, str) or not customer or not isinstance(subscription_id, str) or not subscription_id:
        raise ValueError("Missing subscription identifiers")
    if type(created) is not int or created <= 0:
        raise ValueError("Missing subscription creation timestamp")
    return user_id, customer, subscription_id, created


def _retrieve_subscription(subscription_id):
    client = stripe.StripeClient(settings.STRIPE_SECRET_KEY)
    subscription = client.v1.subscriptions.retrieve(subscription_id)
    return subscription.to_dict_recursive() if hasattr(subscription, "to_dict_recursive") else dict(subscription)


def _revision(client, user_id):
    rows = (
        client.table("subscriptions").select("billing_revision")
        .eq("user_id", user_id).execute().data or []
    )
    if len(rows) > 1:
        raise ValueError("Duplicate subscription rows require reconciliation")
    if not rows:
        return None
    revision = rows[0].get("billing_revision")
    if type(revision) is not int or revision < 0:
        raise RuntimeError("Subscription revision unavailable")
    return revision


def sync_subscription(subscription, *, refresh=None):
    """Compare-and-swap after a canonical read; never retry a stale snapshot."""
    identity = _identity(subscription)
    user_id, customer, subscription_id, created = identity
    client = get_supabase_client()
    revision = _revision(client, user_id)
    # The first read discovers ownership. The second read must happen AFTER the
    # revision read, so a concurrent writer cannot be silently overwritten.
    if refresh is not None:
        subscription = refresh(subscription_id)
        if _identity(subscription) != identity:
            raise ValueError("Subscription identity changed during verification")
    items = (subscription.get("items") or {}).get("data") or []
    price = ((items[0].get("price") or {}).get("id") if items else "") or ""
    status = subscription.get("status") or "inactive"
    plan = map_price_to_plan(price) if status in {"active", "trialing"} and len(items) == 1 else "free"
    result = client.rpc("billing_sync_subscription", {
        "p_user_id": user_id,
        "p_customer": customer,
        "p_subscription": subscription_id,
        "p_subscription_created": created,
        "p_plan": plan,
        "p_status": status,
        "p_expected_revision": revision,
    }).execute().data
    if result == "retry":
        # Stripe will redeliver; do not replay the same stale snapshot here.
        raise RuntimeError("Concurrent subscription update; retry delivery")
    if result not in {"applied", "ignored"}:
        raise RuntimeError("Unexpected subscription persistence outcome")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    if not settings.STRIPE_WEBHOOK_SECRET or not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe webhooks not configured")
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(status_code=503, detail="Billing storage unavailable")
    try:
        event = stripe.Webhook.construct_event(await request.body(), request.headers.get("stripe-signature"), settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.SignatureVerificationError) as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook signature") from exc
    event_type = event["type"]
    if event_type not in EVENT_TYPES:
        return {"ok": True, "event_type": event_type}
    subscription_id = _subscription_id(event)
    if not subscription_id:
        if event_type.startswith("invoice."):
            return {"ok": True, "event_type": event_type}
        raise HTTPException(status_code=422, detail="Missing subscription identifier")
    try:
        if event_type == "customer.subscription.deleted":
            # A signature-verified deletion is terminal for this subscription.
            snapshot = dict(event["data"]["object"])
            snapshot["status"] = "canceled"
            sync_subscription(snapshot)
        else:
            snapshot = _retrieve_subscription(subscription_id)
            if snapshot.get("id") != subscription_id:
                raise ValueError("Subscription identifier mismatch")
            sync_subscription(snapshot, refresh=_retrieve_subscription)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Subscription synchronisation failed") from exc
    return {"ok": True, "event_type": event_type}
