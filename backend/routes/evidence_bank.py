"""Private Evidence Bank routes for reusable candidate examples."""

from __future__ import annotations

from datetime import datetime, timezone
import json
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


class EvidenceImportDraft(EvidenceBase):
    source_filename: str


class EvidenceImportResponse(BaseModel):
    drafts: list[EvidenceImportDraft] = Field(default_factory=list)
    provider: str
    files_processed: int


MAX_IMPORT_FILES = 8
MAX_IMPORT_DRAFTS = 12
MAX_IMPORT_TEXT = 70000


def _clean_import_list(values: Any, *, limit: int = 20) -> list[str]:
    if not isinstance(values, list):
        return []
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = " ".join(str(value).split()).strip(" •·,-")
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            output.append(cleaned[:500])
        if len(output) >= limit:
            break
    return output


def _validate_import_draft(raw: dict[str, Any], filenames: set[str]) -> EvidenceImportDraft | None:
    title = " ".join(str(raw.get("title") or "").split()).strip()
    source_filename = Path(str(raw.get("source_filename") or "")).name
    actions = _clean_import_list(raw.get("actions"), limit=12)
    if not title or source_filename not in filenames or not actions:
        return None

    return EvidenceImportDraft(
        title=title[:140],
        situation=str(raw.get("situation") or "").strip()[:3000],
        task=str(raw.get("task") or "").strip()[:3000],
        actions=actions,
        outcome=str(raw.get("outcome") or "").strip()[:3000],
        reflection=str(raw.get("reflection") or "").strip()[:3000],
        tags=_clean_import_list(raw.get("tags"), limit=20),
        behaviours=_clean_import_list(raw.get("behaviours"), limit=20),
        skills=_clean_import_list(raw.get("skills"), limit=20),
        authority_context=(str(raw.get("authority_context") or "").strip()[:1500] or None),
        source="imported_application",
        confidence=55,
        source_filename=source_filename,
    )


def _openai_import_evidence(documents: list[tuple[str, str]]) -> list[EvidenceImportDraft] | None:
    if not settings.OPENAI_API_KEY:
        return None

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        drafts: list[EvidenceImportDraft] = []
        seen: set[tuple[str, str]] = set()

        # Process every accepted file independently so a large earlier document
        # can never silently truncate examples from later uploads.
        for filename, text in documents:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=3000,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Extract reusable evidence examples from the candidate's existing personal statement or application. "
                            "Use ONLY facts explicitly stated in the supplied document. Do not infer achievements, metrics, seniority, "
                            "authority, qualifications, outcomes, behaviours, tools, or responsibilities that are not stated. "
                            "Do not convert aspirations, vacancy criteria, employer descriptions, or generic claims into experience. "
                            "Split genuinely distinct examples into separate cards. Leave a field blank when the source does not support it. "
                            "Preserve limits on the candidate's authority. Return JSON with key examples, an array of objects with: "
                            "source_filename, title, situation, task, actions (string array), outcome, reflection, tags (string array), "
                            "behaviours (string array), skills (string array), authority_context. Return at most 6 examples."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"=== FILE: {filename} ===\n{text[:MAX_IMPORT_TEXT]}",
                    },
                ],
            )
            parsed = json.loads(response.choices[0].message.content or "{}")
            raw_examples = parsed.get("examples")
            if not isinstance(raw_examples, list):
                continue

            for raw in raw_examples[:6]:
                if not isinstance(raw, dict):
                    continue
                raw["source_filename"] = filename
                draft = _validate_import_draft(raw, {filename})
                if draft is None:
                    continue
                key = (draft.title.casefold(), " ".join(draft.actions).casefold())
                if key in seen:
                    continue
                seen.add(key)
                drafts.append(draft)
                if len(drafts) >= MAX_IMPORT_DRAFTS:
                    return drafts

        return drafts or None
    except Exception:
        return None


def _fallback_import_evidence(documents: list[tuple[str, str]]) -> list[EvidenceImportDraft]:
    drafts: list[EvidenceImportDraft] = []
    for filename, text in documents:
        paragraphs = [
            " ".join(part.split()).strip()
            for part in text.split("\n\n")
            if len(" ".join(part.split()).strip()) >= 100
        ]
        for index, paragraph in enumerate(paragraphs[:3], start=1):
            drafts.append(
                EvidenceImportDraft(
                    title=f"Imported example {index} from {Path(filename).stem}"[:140],
                    actions=[paragraph[:3000]],
                    source="imported_application",
                    confidence=40,
                    source_filename=filename,
                )
            )
            if len(drafts) >= MAX_IMPORT_DRAFTS:
                return drafts
    return drafts


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


@router.post("/import-documents", response_model=EvidenceImportResponse)
async def import_evidence_documents(
    files: list[UploadFile] = File(...),
    authorization: str | None = Header(None),
) -> EvidenceImportResponse:
    await verify_supabase_user(authorization)
    if not files:
        raise HTTPException(status_code=400, detail="Choose at least one application document to import.")
    if len(files) > MAX_IMPORT_FILES:
        raise HTTPException(status_code=400, detail=f"Import up to {MAX_IMPORT_FILES} files at a time.")

    documents: list[tuple[str, str]] = []
    for file in files:
        filename = Path(file.filename or "application").name
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise HTTPException(status_code=415, detail="Upload PDF, DOCX or TXT application documents.")

        data = await file.read(MAX_CV_BYTES + 1)
        if len(data) > MAX_CV_BYTES:
            raise HTTPException(status_code=413, detail=f"{filename} must be 5 MB or smaller.")
        documents.append((filename, _extract_text(filename, data)))

    drafts = _openai_import_evidence(documents)
    provider = "openai" if drafts is not None else "fallback"
    if drafts is None:
        drafts = _fallback_import_evidence(documents)
    if not drafts:
        raise HTTPException(
            status_code=422,
            detail="We could read these files but could not identify a reusable experience example.",
        )

    return EvidenceImportResponse(
        drafts=drafts,
        provider=provider,
        files_processed=len(documents),
    )


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