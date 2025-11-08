"""Stripe webhook receiver for JobSleuth AI backend.

This endpoint handles events from Stripe. Extend it to react to invoice
payments, subscription updates, etc. Make sure to configure your Stripe
dashboard to send webhooks to this URL.

Returns deterministic JSON responses for plan mapping.
"""

import os
import stripe
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any

router = APIRouter(prefix="/stripe")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_xxx")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_xxx")

# Deterministic plan mapping from Stripe price IDs to internal plan names
PLAN_MAPPING: Dict[str, str] = {
    os.getenv("NEXT_PUBLIC_STRIPE_PRICE_PRO", "price_pro_xxx"): "pro",
    os.getenv("NEXT_PUBLIC_STRIPE_PRICE_INVESTOR", "price_investor_xxx"): "investor",
}


def map_price_to_plan(price_id: str) -> str:
    """Map Stripe price ID to internal plan name.
    
    Args:
        price_id: Stripe price ID
        
    Returns:
        Internal plan name (pro, investor, or free)
    """
    return PLAN_MAPPING.get(price_id, "free")


def create_deterministic_response(
    status: str,
    event_type: str,
    data: Dict[str, Any] = None
) -> JSONResponse:
    """Create a deterministic JSON response.
    
    Ensures consistent key ordering and structure.
    
    Args:
        status: Status message
        event_type: Stripe event type
        data: Additional data
        
    Returns:
        JSONResponse with deterministic structure
    """
    response = {
        "status": status,
        "event_type": event_type,
    }
    
    if data:
        # Sort keys to ensure deterministic order
        response["data"] = {k: data[k] for k in sorted(data.keys())}
    
    return JSONResponse(response)


@router.post("/webhook")
async def stripe_webhook(request: Request) -> JSONResponse:
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError as exc:
        # Invalid payload
        raise HTTPException(status_code=400, detail=str(exc))
    except stripe.error.SignatureVerificationError as exc:
        # Invalid signature
        raise HTTPException(status_code=400, detail=str(exc))

    event_type = event['type']
    
    # Handle the event with deterministic responses
    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        
        # Get subscription details to map to plan
        plan = "free"
        if subscription_id:
            try:
                subscription = stripe.Subscription.retrieve(subscription_id)
                if subscription.items.data:
                    price_id = subscription.items.data[0].price.id
                    plan = map_price_to_plan(price_id)
            except Exception as e:
                print(f"Error retrieving subscription: {e}")
        
        return create_deterministic_response(
            "success",
            event_type,
            {
                "customer_id": customer_id,
                "plan": plan,
                "subscription_id": subscription_id,
            }
        )
    
    elif event_type == 'invoice.paid':
        invoice = event['data']['object']
        customer_id = invoice.get('customer')
        subscription_id = invoice.get('subscription')
        
        return create_deterministic_response(
            "success",
            event_type,
            {
                "customer_id": customer_id,
                "subscription_id": subscription_id,
            }
        )
    
    elif event_type == 'customer.subscription.updated':
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        
        # Map price to plan
        plan = "free"
        if subscription.get('items', {}).get('data'):
            price_id = subscription['items']['data'][0]['price']['id']
            plan = map_price_to_plan(price_id)
        
        return create_deterministic_response(
            "success",
            event_type,
            {
                "customer_id": customer_id,
                "plan": plan,
                "status": subscription.get('status'),
            }
        )
    
    elif event_type == 'customer.subscription.deleted':
        subscription = event['data']['object']
        customer_id = subscription.get('customer')
        
        return create_deterministic_response(
            "success",
            event_type,
            {
                "customer_id": customer_id,
                "plan": "free",  # Revert to free plan
            }
        )
    
    # Return success for unhandled events (but with deterministic structure)
    return create_deterministic_response("success", event_type)

