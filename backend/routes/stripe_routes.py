import stripe
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from lib.settings import settings

router = APIRouter(prefix="/stripe")

stripe.api_key = settings.STRIPE_SECRET_KEY or None


class CheckoutRequest(BaseModel):
    price_id: str
    email: str | None = None


@router.post("/checkout")
async def create_checkout_session(request: CheckoutRequest) -> JSONResponse:
    if not settings.STRIPE_SECRET_KEY:
        return JSONResponse({"ok": False, "error": "stripe_not_configured"}, status_code=200)
    try:
        session = stripe.checkout.Session.create(
            line_items=[{"price": request.price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{settings.FRONTEND_URL}/account?success=true&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/pricing?canceled=true",
            customer_creation="always",
            customer_email=request.email,
        )
        return JSONResponse({"ok": True, "url": session.url})
    except Exception:
        return JSONResponse({"ok": False, "error": "checkout_failed"}, status_code=200)
