"""Private pilot feedback capture for JobSleuth validation."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from lib.supabase import get_supabase_client
from routes.saved_jobs import verify_supabase_user

router = APIRouter(prefix="/pilot-feedback", tags=["pilot_feedback"])


class PilotFeedbackCreate(BaseModel):
    provider: str = Field(default="", max_length=80)
    recommendation: str = Field(default="", max_length=40)
    application_type: str = Field(default="", max_length=80)
    word_count: int = Field(default=0, ge=0, le=5000)
    usefulness: int = Field(ge=1, le=10)
    would_submit: bool
    recommendation_trust: bool
    material_time_saving: bool
    would_use_again: bool
    payment_signal: Literal["yes", "maybe", "no"]


@router.post("", status_code=201)
async def create_pilot_feedback(
    request: PilotFeedbackCreate,
    authorization: str | None = Header(None),
) -> dict[str, bool]:
    user = await verify_supabase_user(authorization)
    payload = request.model_dump()
    payload["user_id"] = user["id"]
    get_supabase_client().table("pilot_feedback").insert(payload).execute()
    return {"ok": True}
