"""Stripe webhook receiver for JobSleuth AI backend.

This endpoint handles events from Stripe. Extend it to react to invoice
payments, subscription updates, etc. Make sure to configure your Stripe
dashboard to send webhooks to this URL.
"""

import os

import stripe
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from lib.settings import settings
from lib.supabase import supabase_admin

router = APIRouter(prefix="/stripe")

stripe.api_key = settings.STRIPE_SECRET_KEY
webhook_secret = settings.STRIPE_WEBHOOK_SECRET


@router.post("/webhook")
async def stripe_webhook(request: Request) -> JSONResponse:
    """Handle Stripe webhook events with deterministic responses."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        # Invalid payload
        return JSONResponse({"ok": False, "error": "Invalid payload"}, status_code=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return JSONResponse({"ok": False, "error": "Invalid signature"}, status_code=400)
    
    # Handle the event
    try:
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            
            # Extract customer info
            customer_id = session.get("customer")
            customer_email = session.get("customer_email") or session.get("customer_details", {}).get("email")
            
            # Determine plan from price_id
            price_id = None
            if session.get("line_items"):
                price_id = session["line_items"]["data"][0]["price"]["id"]
            elif session.get("amount_total"):
                # Fallback: try to get from metadata or subscription
                subscription_id = session.get("subscription")
                if subscription_id:
                    subscription = stripe.Subscription.retrieve(subscription_id)
                    price_id = subscription["items"]["data"][0]["price"]["id"]
            
            # Map price_id to plan
            plan = "free"
            if price_id == settings.PRICE_ID_PRO:
                plan = "pro"
            elif price_id == settings.PRICE_ID_INVESTOR:
                plan = "investor"
            
            # Update user in database
            if customer_email:
                supabase_admin.table("users").upsert({
                    "email": customer_email,
                    "plan": plan,
                    "stripe_customer_id": customer_id,
                }, on_conflict="email").execute()
        
        elif event["type"] == "customer.subscription.updated":
            subscription = event["data"]["object"]
            customer_id = subscription.get("customer")
            
            # Get price_id from subscription
            price_id = subscription["items"]["data"][0]["price"]["id"]
            
            # Map price_id to plan
            plan = "free"
            if price_id == settings.PRICE_ID_PRO:
                plan = "pro"
            elif price_id == settings.PRICE_ID_INVESTOR:
                plan = "investor"
            
            # Update user by stripe_customer_id
            if customer_id:
                supabase_admin.table("users")\
                    .update({"plan": plan})\
                    .eq("stripe_customer_id", customer_id)\
                    .execute()
        
        elif event["type"] == "customer.subscription.deleted":
            subscription = event["data"]["object"]
            customer_id = subscription.get("customer")
            
            # Downgrade to free
            if customer_id:
                supabase_admin.table("users")\
                    .update({"plan": "free"})\
                    .eq("stripe_customer_id", customer_id)\
                    .execute()
        
        # Return success for handled events
        return JSONResponse({"ok": True})
    
    except Exception as e:
        # Return error but with 200 status (to avoid Stripe retries for invalid data)
        return JSONResponse({"ok": False, "error": str(e)}, status_code=200)

