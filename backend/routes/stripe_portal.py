import stripe
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from lib.settings import settings

router = APIRouter(prefix="/stripe")

stripe.api_key = settings.STRIPE_SECRET_KEY or None


class PortalRequest(BaseModel):
    customer_id: str | None = None


@router.post("/create-portal-session")
async def create_portal_session(request: PortalRequest) -> JSONResponse:
    if not settings.STRIPE_SECRET_KEY:
        return JSONResponse({"ok": False, "error": "stripe_not_configured"}, status_code=200)
    if not request.customer_id:
        return JSONResponse({"ok": False, "error": "customer_id_required"}, status_code=200)
    try:
        session = stripe.billing_portal.Session.create(
            customer=request.customer_id,
            return_url=f"{settings.FRONTEND_URL}/account",
        )
        return JSONResponse({"ok": True, "url": session.url})
    except Exception:
        return JSONResponse({"ok": False, "error": "portal_failed"}, status_code=200)
