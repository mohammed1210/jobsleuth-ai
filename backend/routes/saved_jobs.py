"""Saved Jobs backed by real Supabase data and verified Auth tokens.

Production routes never return sample rows or report success after a database
failure. The legacy /saved alias shares the same safe implementation.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from lib.settings import settings
from lib.supabase import get_supabase_client

router = APIRouter(prefix="/saved-jobs", tags=["saved_jobs"])
legacy_router = APIRouter(prefix="/saved", tags=["saved_jobs_legacy"])


class SavedJobRequest(BaseModel):
    job_id: int


class SavedJobResponse(BaseModel):
    id: int
    user_id: str
    job_id: int
    saved_at: str
    job: dict[str, Any] | None = None


def _extract_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization Bearer token required")
    token = authorization.removeprefix("Bearer ").strip()
    if not token or token == "invalid":
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token


async def verify_supabase_user(authorization: str | None) -> dict[str, str]:
    """Validate the token against the *configured* Supabase Auth project."""
    token = _extract_token(authorization)
    if not settings.SUPABASE_URL or not (settings.SUPABASE_KEY or settings.SUPABASE_SERVICE_ROLE_KEY):
        raise HTTPException(status_code=503, detail="Authentication provider is not configured")

    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": settings.SUPABASE_KEY or settings.SUPABASE_SERVICE_ROLE_KEY,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user", headers=headers
            )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Authentication provider unavailable") from exc

    if response.status_code >= 500:
        raise HTTPException(status_code=503, detail="Authentication provider unavailable")
    if response.status_code >= 400:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    try:
        data = response.json()
        user_id = str(UUID(data["id"]))
        if not data.get("email"):
            raise ValueError("Verified email is required")
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid identity response") from exc
    return {"id": user_id, "email": str(data["email"])}


def _storage_unavailable(action: str, exc: Exception | None = None) -> HTTPException:
    return HTTPException(status_code=503, detail=f"Saved Jobs storage unavailable during {action}")


def _map_record(row: dict[str, Any]) -> SavedJobResponse:
    record = dict(row)
    if "jobs" in record:
        record["job"] = record.pop("jobs")
    if "job" not in record or record["job"] is None:
        raise _storage_unavailable("reading job details")
    try:
        return SavedJobResponse(**record)
    except (ValueError, TypeError) as exc:
        raise _storage_unavailable("parsing saved jobs", exc) from exc


async def _list_saved(authorization: str | None) -> list[SavedJobResponse]:
    user = await verify_supabase_user(authorization)
    try:
        result = (
            get_supabase_client().table("saved_jobs")
            .select("*, jobs(*)").eq("user_id", user["id"]).execute()
        )
        return [_map_record(row) for row in (result.data or [])]
    except HTTPException:
        raise
    except Exception as exc:
        raise _storage_unavailable("listing", exc) from exc


async def _save_job(request: SavedJobRequest, authorization: str | None) -> SavedJobResponse:
    user = await verify_supabase_user(authorization)
    try:
        storage = get_supabase_client()
        jobs = (
            storage.table("live_jobs").select("id")
            .eq("id", request.job_id).limit(1).execute()
        )
        if not jobs.data:
            raise HTTPException(status_code=404, detail="Job is unavailable or no longer accepting applications")
        saved = (
            storage.table("saved_jobs")
            .upsert({"user_id": user["id"], "job_id": request.job_id},
                    on_conflict="user_id,job_id")
            .execute()
        )
        if not saved.data:
            raise _storage_unavailable("saving")
        return SavedJobResponse(**saved.data[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise _storage_unavailable("saving", exc) from exc


async def _delete_saved(job_id: int, authorization: str | None) -> dict[str, bool]:
    user = await verify_supabase_user(authorization)
    try:
        (
            get_supabase_client().table("saved_jobs")
            .delete().eq("user_id", user["id"]).eq("job_id", job_id).execute()
        )
    except Exception as exc:
        raise _storage_unavailable("deleting", exc) from exc
    return {"ok": True}


@router.get("", response_model=list[SavedJobResponse])
async def list_saved_jobs(authorization: str | None = Header(None)) -> list[SavedJobResponse]:
    return await _list_saved(authorization)


@router.post("", response_model=SavedJobResponse)
async def save_job(request: SavedJobRequest, authorization: str | None = Header(None)) -> SavedJobResponse:
    return await _save_job(request, authorization)


@router.delete("/{job_id}")
async def unsave_job(job_id: int, authorization: str | None = Header(None)) -> dict[str, bool]:
    return await _delete_saved(job_id, authorization)


legacy_router.add_api_route("", list_saved_jobs, methods=["GET"], response_model=list[SavedJobResponse])
legacy_router.add_api_route("", save_job, methods=["POST"], response_model=SavedJobResponse)
legacy_router.add_api_route("/{job_id}", unsave_job, methods=["DELETE"])
