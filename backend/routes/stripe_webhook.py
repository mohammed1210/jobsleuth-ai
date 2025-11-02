"""Stripe webhook receiver for JobSleuth AI backend.

This endpoint handles events from Stripe. Extend it to react to invoice
payments, subscription updates, etc. Make sure to configure your Stripe
dashboard to send webhooks to this URL.
"""

import os
import stripe
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/stripe")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_xxx")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_xxx")

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

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        # TODO: handle successful checkout
        pass
    elif event['type'] == 'invoice.paid':
        # TODO: handle paid invoice
        pass
    # Add more event handlers as needed

    return JSONResponse({"status": "success"})
