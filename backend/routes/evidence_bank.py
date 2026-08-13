"""Private Evidence Bank routes for reusable candidate examples."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from lib.supabase import get_supabase_client
from routes.saved_jobs import verify_supabase_user

router = APIRouter(prefix="/evidence", tags=["evidence_bank"])


class EvidenceBase(BaseModel):
    title: str = Field(min_length=1, max_length=140)
    situation: str = ""
    task: str = ""
    actions: list[str] = Field(default_factory=list)
    outcome: str = ""
    reflection: str = ""
    tags: list[str] = Field(default_factory=list)
    behaviours: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    authority_context: str | None = None
    source: str = "manual"
    confidence: int = Field(default=70, ge=0, le=100)


class EvidenceCreate(EvidenceBase):
    pass


class EvidenceUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=140)
    situation: str | None = None
    task: str | None = None
    actions: list[str] | None = None
    outcome: str | None = None
    reflection: str | None = None
    tags: list[str] | None = None
    behaviours: list[str] | None = None
    skills: list[str] | None = None
    authority_context: str | None = None
    source: str | None = None
    confidence: int | None = Field(default=None, ge=0, le=100)


class EvidenceResponse(EvidenceBase):
    id: str
    user_id: str
    created_at: datetime | str | None = None
    updated_at: datetime | str | None = None


def _db() -> Any:
    return get_supabase_client()


def _require_persistence(result: Any, *, action: str) -> list[dict[str, Any]]:
    rows = getattr(result, "data", None) or []
    if not rows:
        raise HTTPException(
            status_code=503,
            detail=f"Evidence Bank persistence unavailable during {action}. Try again later.",
        )
    return rows


@router.get("", response_model=list[EvidenceResponse])
async def list_evidence(authorization: str | None = Header(None)) -> list[EvidenceResponse]:
    user = await verify_supabase_user(authorization)
    result = _db().table("evidence_cards").select("*").eq("user_id", user["id"]).execute()
    rows = getattr(result, "data", None) or []
    rows = sorted(rows, key=lambda row: str(row.get("updated_at") or ""), reverse=True)
    return [EvidenceResponse(**row) for row in rows]


@router.post("", response_model=EvidenceResponse, status_code=201)
async def create_evidence(
    request: EvidenceCreate,
    authorization: str | None = Header(None),
) -> EvidenceResponse:
    user = await verify_supabase_user(authorization)
    payload = request.model_dump()
    payload["user_id"] = user["id"]
    result = _db().table("evidence_cards").insert(payload).execute()
    row = _require_persistence(result, action="create")[0]
    return EvidenceResponse(**row)


@router.patch("/{evidence_id}", response_model=EvidenceResponse)
async def update_evidence(
    evidence_id: str,
    request: EvidenceUpdate,
    authorization: str | None = Header(None),
) -> EvidenceResponse:
    user = await verify_supabase_user(authorization)
    payload = request.model_dump(exclude_unset=True)
    if not payload:
        raise HTTPException(status_code=400, detail="No evidence fields supplied")
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = (
        _db()
        .table("evidence_cards")
        .update(payload)
        .eq("id", evidence_id)
        .eq("user_id", user["id"])
        .execute()
    )
    rows = getattr(result, "data", None) or []
    if not rows:
        raise HTTPException(status_code=404, detail="Evidence card not found")
    return EvidenceResponse(**rows[0])


@router.delete("/{evidence_id}")
async def delete_evidence(
    evidence_id: str,
    authorization: str | None = Header(None),
) -> dict[str, bool]:
    user = await verify_supabase_user(authorization)
    result = (
        _db()
        .table("evidence_cards")
        .delete()
        .eq("id", evidence_id)
        .eq("user_id", user["id"])
        .execute()
    )
    rows = getattr(result, "data", None) or []
    if not rows:
        raise HTTPException(status_code=404, detail="Evidence card not found")
    return {"ok": True}
