"""Stripe customer portal route for JobSleuth AI backend."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import stripe
import os

router = APIRouter(prefix="/stripe")

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_xxx")

@router.post("/create-portal-session")
async def create_portal_session(customer_id: str) -> JSONResponse:
    """Create a Stripe billing portal session for an existing customer."""
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=os.getenv("FRONTEND_URL", "http://localhost:3000") + "/account",
        )
        return JSONResponse({"url": session.url})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
