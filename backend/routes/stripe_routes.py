"""Stripe checkout routes for JobSleuth AI backend.

These routes handle creation of checkout sessions for subscription plans.
Replace the placeholder pricing IDs with your actual Stripe Price IDs.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import stripe
import os

router = APIRouter(prefix="/stripe")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_xxx")

@router.post("/checkout")
async def create_checkout_session(price_id: str) -> JSONResponse:
    """Create a Stripe Checkout session for the given price ID."""
    try:
        session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=os.getenv("FRONTEND_URL", "http://localhost:3000") + "/account?status=success",
            cancel_url=os.getenv("FRONTEND_URL", "http://localhost:3000") + "/account?status=cancel",
            customer_creation="always",
        )
        return JSONResponse({"url": session.url})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
