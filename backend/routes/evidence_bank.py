"""Private Evidence Bank routes for reusable candidate examples."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field

from lib.settings import settings
from lib.supabase import get_supabase_client
from routes.candidate_profile import ALLOWED_SUFFIXES, MAX_CV_BYTES, _extract_text
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


class EvidenceImportDraft(BaseModel):
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
    confidence: int = Field(default=55, ge=0, le=100)
    source_excerpt: str = ""


class EvidenceImportResponse(BaseModel):
    source_filename: str
    extraction_provider: str
    drafts: list[EvidenceImportDraft] = Field(default_factory=list)


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


def _dedupe_text(values: list[str], *, limit: int = 12) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = re.sub(r"\s+", " ", str(value)).strip(" \t\n•·,-")
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            output.append(cleaned[:500])
        if len(output) >= limit:
            break
    return output


def _normalise_import_draft(raw: dict[str, Any], index: int, source_text: str) -> EvidenceImportDraft | None:
    actions = _dedupe_text([str(item) for item in (raw.get("actions") or []) if item], limit=8)
    situation = re.sub(r"\s+", " ", str(raw.get("situation") or "")).strip()[:1200]
    task = re.sub(r"\s+", " ", str(raw.get("task") or "")).strip()[:1200]
    outcome = re.sub(r"\s+", " ", str(raw.get("outcome") or "")).strip()[:1200]
    reflection = re.sub(r"\s+", " ", str(raw.get("reflection") or "")).strip()[:1200]
    authority_context = re.sub(r"\s+", " ", str(raw.get("authority_context") or "")).strip()[:800] or None
    excerpt = re.sub(r"\s+", " ", str(raw.get("source_excerpt") or "")).strip()[:2200]
    normalised_source = re.sub(r"\s+", " ", source_text).strip().casefold()
    if not excerpt or excerpt.casefold() not in normalised_source:
        return None
    if not any((situation, task, actions, outcome, reflection, authority_context)):
        return None

    title = re.sub(r"\s+", " ", str(raw.get("title") or "")).strip()[:140]
    if not title:
        title = f"Imported application example {index + 1}"

    return EvidenceImportDraft(
        title=title,
        situation=situation,
        task=task,
        actions=actions,
        outcome=outcome,
        reflection=reflection,
        tags=_dedupe_text([str(item) for item in (raw.get("tags") or []) if item], limit=12),
        behaviours=_dedupe_text([str(item) for item in (raw.get("behaviours") or []) if item], limit=12),
        skills=_dedupe_text([str(item) for item in (raw.get("skills") or []) if item], limit=12),
        authority_context=authority_context,
        confidence=55,
        source_excerpt=excerpt,
    )


def _openai_evidence_import(text: str, filename: str) -> list[EvidenceImportDraft] | None:
    if not settings.OPENAI_API_KEY:
        return None
    source = text[:45000]
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=5000,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract reusable candidate evidence examples from a previously written job application or personal statement. "
                        "Use only facts explicitly stated in the supplied source. Do not invent outcomes, numbers, authority, seniority, "
                        "stakeholders, skills or reflections. Preserve first-person ownership accurately and do not upgrade language such "
                        "as 'supported', 'contributed', or 'recommended' into 'led', 'managed', 'approved', or 'decided'. "
                        "Identify distinct real examples rather than generic claims. For each example return: title, situation, task, "
                        "actions (array), outcome, reflection, tags (array), behaviours (array), skills (array), authority_context, "
                        "and source_excerpt. Leave any field empty if the source does not state it. source_excerpt should be a short "
                        "verbatim excerpt from the source that lets the user verify the extraction. Return JSON with key drafts containing "
                        "at most 12 examples."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Source filename: {filename}\n\n{source}",
                },
            ],
        )
        parsed = json.loads(response.choices[0].message.content or "{}")
        drafts_raw = parsed.get("drafts") if isinstance(parsed, dict) else None
        if not isinstance(drafts_raw, list):
            return []
        drafts: list[EvidenceImportDraft] = []
        seen: set[str] = set()
        for index, raw in enumerate(drafts_raw[:12]):
            if not isinstance(raw, dict):
                continue
            draft = _normalise_import_draft(raw, index, source)
            if draft is None:
                continue
            key = "|".join(
                [
                    draft.title.casefold(),
                    draft.situation.casefold()[:160],
                    " ".join(draft.actions).casefold()[:240],
                ]
            )
            if key in seen:
                continue
            seen.add(key)
            drafts.append(draft)
        return drafts
    except Exception:
        return None


def _fallback_star_import(text: str) -> list[EvidenceImportDraft]:
    """Conservative fallback for documents that already use explicit STAR headings."""

    situation_starts = list(re.finditer(r"(?im)^\s*situation\s*:", text))
    if situation_starts:
        chunks = [
            text[match.start() : (situation_starts[index + 1].start() if index + 1 < len(situation_starts) else len(text))]
            for index, match in enumerate(situation_starts)
        ]
    else:
        chunks = [text]

    drafts: list[EvidenceImportDraft] = []
    for chunk in chunks:
        lowered = chunk.casefold()
        if not ("situation:" in lowered and ("action:" in lowered or "actions:" in lowered) and ("result:" in lowered or "outcome:" in lowered)):
            continue

        def field(*labels: str) -> str:
            for label in labels:
                match = re.search(
                    rf"(?is)(?:^|\n)\s*{re.escape(label)}\s*:\s*(.+?)(?=\n\s*(?:situation|task|responsibility|action|actions|result|outcome|reflection|learning)\s*:|$)",
                    chunk,
                )
                if match:
                    return re.sub(r"\s+", " ", match.group(1)).strip()
            return ""

        situation = field("situation")
        task = field("task", "responsibility")
        action_text = field("action", "actions")
        outcome = field("result", "outcome")
        reflection = field("reflection", "learning")
        if not any((situation, task, action_text, outcome)):
            continue
        drafts.append(
            EvidenceImportDraft(
                title=f"Imported application example {len(drafts) + 1}",
                situation=situation,
                task=task,
                actions=[action_text] if action_text else [],
                outcome=outcome,
                reflection=reflection,
                confidence=50,
                source_excerpt=re.sub(r"\s+", " ", chunk).strip()[:2200],
            )
        )
        if len(drafts) >= 12:
            break
    return drafts


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
    rows = [row for row in rows if row.get("source") != "cv_profile"]
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


@router.post("/import", response_model=EvidenceImportResponse)
async def import_evidence_document(
    file: UploadFile = File(...),
    authorization: str | None = Header(None),
) -> EvidenceImportResponse:
    await verify_supabase_user(authorization)
    filename = Path(file.filename or "application").name
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=415, detail="Upload a PDF, DOCX or TXT application or personal statement.")

    data = await file.read(MAX_CV_BYTES + 1)
    if len(data) > MAX_CV_BYTES:
        raise HTTPException(status_code=413, detail="Application files must be 5 MB or smaller.")

    try:
        text = _extract_text(filename, data)
    except HTTPException as exc:
        if exc.status_code in {415, 413}:
            raise
        raise HTTPException(
            status_code=422,
            detail="Could not read enough text from this application. Try a standard PDF, DOCX or TXT file.",
        ) from exc

    drafts = _openai_evidence_import(text, filename)
    provider = "openai"
    if drafts is None:
        drafts = _fallback_star_import(text)
        provider = "star-fallback"

    if not drafts:
        raise HTTPException(
            status_code=422,
            detail=(
                "JobSleuth could read this file but could not reliably identify a reusable evidence example. "
                "Try another personal statement or an application containing a specific example."
            ),
        )

    return EvidenceImportResponse(
        source_filename=filename,
        extraction_provider=provider,
        drafts=drafts,
    )


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