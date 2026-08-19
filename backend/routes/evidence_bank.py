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


_VACANCY_MARKERS = (
    "role summary",
    "job summary",
    "essential criteria",
    "essential requirements",
    "desirable criteria",
    "trainable requirements",
    "practical requirements",
    "eligibility",
    "successful candidate",
    "successful applicant",
    "applicants must",
    "we are looking for",
    "application closing date",
    "salary minimum",
    "salary maximum",
)


def _combined_evidence_text(payload: dict[str, Any]) -> str:
    values: list[str] = []
    for key in ("title", "situation", "task", "outcome", "reflection", "authority_context"):
        value = payload.get(key)
        if value:
            values.append(str(value))
    values.extend(str(item) for item in (payload.get("actions") or []) if item)
    return "\n".join(values).lower()


def _looks_like_vacancy_text(payload: dict[str, Any]) -> bool:
    """Detect obvious job adverts accidentally pasted into the Evidence Bank.

    This is intentionally conservative: one phrase such as "successful candidate"
    is not enough. Multiple advert-section/candidate markers must be present before
    the save is rejected.
    """

    text = _combined_evidence_text(payload)
    matches = {marker for marker in _VACANCY_MARKERS if marker in text}
    section_markers = {
        "role summary",
        "job summary",
        "essential criteria",
        "essential requirements",
        "desirable criteria",
        "trainable requirements",
        "practical requirements",
        "eligibility",
    }
    candidate_markers = {
        "successful candidate",
        "successful applicant",
        "applicants must",
        "we are looking for",
    }
    return len(matches) >= 3 or (
        len(matches & section_markers) >= 2 and bool(matches & candidate_markers)
    )


def _reject_vacancy_contamination(payload: dict[str, Any]) -> None:
    if _looks_like_vacancy_text(payload):
        raise HTTPException(
            status_code=422,
            detail=(
                "This looks like a vacancy advert, not personal evidence. Paste job adverts into "
                "JobSleuth Apply and keep the Evidence Bank for examples from your own experience."
            ),
        )


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
    _reject_vacancy_contamination(payload)
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

    current_result = (
        _db()
        .table("evidence_cards")
        .select("*")
        .eq("id", evidence_id)
        .eq("user_id", user["id"])
        .execute()
    )
    current_rows = getattr(current_result, "data", None) or []
    if not current_rows:
        raise HTTPException(status_code=404, detail="Evidence card not found")
    combined = {**current_rows[0], **payload}
    _reject_vacancy_contamination(combined)

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