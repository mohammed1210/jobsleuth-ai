"""Verified user profiles and free/paid plan information."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from lib.supabase import get_supabase_client
from routes.saved_jobs import verify_supabase_user

router = APIRouter(prefix="/users", tags=["users"])


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    desired_title: str | None = Field(default=None, max_length=140)
    location: str | None = Field(default=None, max_length=140)


@router.get("/me/plan")
async def get_user_plan(authorization: Optional[str] = Header(None)) -> dict:
    """Return verified entitlements (never a mock paid plan)."""
    from lib.billing_entitlements import get_entitlements
    return await get_entitlements(authorization)


@router.get("/me")
async def get_user_profile(authorization: Optional[str] = Header(None)) -> dict:
    user = await verify_supabase_user(authorization)
    try:
        response = (
            get_supabase_client().table("user_profiles")
            .select("full_name,desired_title,location,created_at")
            .eq("user_id", user["id"]).limit(1).execute()
        )
        rows = response.data or []
        if len(rows) > 1:
            raise HTTPException(status_code=503, detail="Profile records require reconciliation")
        record = rows[0] if rows else {}
        return {
            "user_id": user["id"],
            "email": user["email"],
            "name": record.get("full_name"),
            "desired_title": record.get("desired_title"),
            "location": record.get("location"),
            "created_at": record.get("created_at"),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Profile storage unavailable") from exc


@router.put("/me")
async def update_user_profile(
    profile_data: ProfileUpdate, authorization: Optional[str] = Header(None)
) -> dict:
    user = await verify_supabase_user(authorization)
    changes = profile_data.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=422, detail="Provide at least one profile field")
    if "name" in changes:
        changes["full_name"] = changes.pop("name")
    changes["updated_at"] = datetime.now(timezone.utc).isoformat()
    try:
        response = (
            get_supabase_client().table("user_profiles")
            .upsert({"user_id": user["id"], **changes}, on_conflict="user_id")
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=503, detail="Profile update was not persisted")
        return {"status": "success", "user_id": user["id"],
                "updated_fields": sorted(set(changes) - {"updated_at"})}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Profile storage unavailable") from exc
