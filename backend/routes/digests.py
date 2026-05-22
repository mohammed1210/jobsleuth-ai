"""Digest routes for JobSleuth AI."""

from fastapi import APIRouter, Header, HTTPException, Query

from lib.settings import settings
from services.emailer import send_digest_email

router = APIRouter(prefix="/digests", tags=["digests"])


@router.get("/test")
async def digest_import_test() -> dict[str, bool | str]:
    return {"ok": True, "send_digest_email_imported": callable(send_digest_email)}


@router.post("/run")
async def run_digest(
    email: str = Query(..., description="Email address to send a test digest to"),
    authorization: str = Header(""),
) -> dict[str, bool | str]:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    if authorization.removeprefix("Bearer ") != settings.AUTH_SCRAPER_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")

    sent = await send_digest_email(
        email,
        [{"title": "Senior Software Engineer", "company": "ExampleCo"}],
    )
    return {"ok": sent, "message": "sent" if sent else "email not configured"}
