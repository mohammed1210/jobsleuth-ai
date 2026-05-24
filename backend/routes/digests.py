"""Digest routes for JobSleuth AI."""

from fastapi import APIRouter, Header, HTTPException, Query

from lib.settings import settings

try:
    from services.emailer import send_digest_email
except ImportError:
    from services.emailer import get_emailer

    async def send_digest_email(to_email: str, jobs: list[dict] | None = None) -> bool:
        result = get_emailer().send_job_digest(to_email, "JobSleuth user", jobs or [])
        if hasattr(result, "__await__"):
            return await result
        return bool(result)

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
