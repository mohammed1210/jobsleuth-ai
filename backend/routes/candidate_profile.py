"""Candidate CV profile routes.

Raw CV files are processed transiently and are not stored. Only a structured
candidate profile is persisted for vacancy matching.
"""

from __future__ import annotations

import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field

from lib.settings import settings
from lib.supabase import get_supabase_client
from routes.saved_jobs import verify_supabase_user

router = APIRouter(prefix="/candidate-profile", tags=["candidate_profile"])

MAX_CV_BYTES = 5 * 1024 * 1024
ALLOWED_SUFFIXES = {".pdf", ".docx", ".txt"}


class CandidateExperience(BaseModel):
    role: str = ""
    organisation: str = ""
    dates: str = ""
    highlights: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)


class CandidateQualification(BaseModel):
    name: str
    institution: str = ""
    date: str = ""


class CandidateProfileData(BaseModel):
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    experience: list[CandidateExperience] = Field(default_factory=list)
    qualifications: list[CandidateQualification] = Field(default_factory=list)


class CandidateProfileResponse(CandidateProfileData):
    user_id: str
    source_filename: str = ""
    extraction_provider: str = "fallback"
    updated_at: datetime | str | None = None


def _db() -> Any:
    return get_supabase_client()


def _dedupe(values: list[str], *, limit: int = 40) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = re.sub(r"\s+", " ", str(value)).strip(" \t\n•·,-")
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            output.append(cleaned[:180])
        if len(output) >= limit:
            break
    return output


def _extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _extract_docx(data: bytes) -> str:
    from docx import Document

    document = Document(io.BytesIO(data))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def _extract_text(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        text = _extract_pdf(data)
    elif suffix == ".docx":
        text = _extract_docx(data)
    elif suffix == ".txt":
        text = data.decode("utf-8", errors="replace")
    else:
        raise HTTPException(status_code=415, detail="Upload a PDF, DOCX or TXT CV.")

    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) < 80:
        raise HTTPException(status_code=422, detail="Could not extract enough readable text from this CV.")
    return text[:50000]


_SECTION_RE = re.compile(
    r"(?im)^\s*(skills|key skills|technical skills|core skills|experience|employment history|work experience|"
    r"qualifications|education|certifications|professional qualifications|profile|summary)\s*:?\s*$"
)


def _sections(text: str) -> dict[str, str]:
    matches = list(_SECTION_RE.finditer(text))
    if not matches:
        return {}
    output: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = match.group(1).lower()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        output[heading] = text[start:end].strip()
    return output


def _fallback_profile(text: str) -> CandidateProfileData:
    sections = _sections(text)
    skills_text = next((sections[key] for key in ("skills", "key skills", "technical skills", "core skills") if key in sections), "")
    skill_parts = re.split(r"[,|;\n•·]+", skills_text)
    skills = _dedupe([part for part in skill_parts if 1 < len(part.strip()) < 80], limit=30)

    qualification_text = next(
        (sections[key] for key in ("qualifications", "education", "certifications", "professional qualifications") if key in sections),
        "",
    )
    qualifications = [
        CandidateQualification(name=line)
        for line in _dedupe(qualification_text.splitlines(), limit=12)
        if len(line) >= 3
    ]

    experience_text = next(
        (sections[key] for key in ("experience", "employment history", "work experience") if key in sections),
        "",
    )
    experience_lines = _dedupe(experience_text.splitlines(), limit=30)
    experience: list[CandidateExperience] = []
    if experience_lines:
        experience.append(
            CandidateExperience(
                role="CV experience",
                highlights=experience_lines[:20],
                skills=skills[:12],
            )
        )

    summary_text = next((sections[key] for key in ("profile", "summary") if key in sections), "")
    summary = " ".join(summary_text.split())[:1200]
    if not summary:
        summary = " ".join(text.split())[:700]

    return CandidateProfileData(
        summary=summary,
        skills=skills,
        experience=experience,
        qualifications=qualifications,
    )


def _openai_profile(text: str) -> CandidateProfileData | None:
    if not settings.OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=1800,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract only facts explicitly present in the candidate CV. "
                        "Do not infer seniority, qualifications, skills, dates, employers or achievements that are not stated. "
                        "Return JSON with keys summary (string), skills (string array), experience "
                        "(array of objects with role, organisation, dates, highlights string array, skills string array), "
                        "and qualifications (array of objects with name, institution, date)."
                    ),
                },
                {"role": "user", "content": text},
            ],
        )
        raw = response.choices[0].message.content or "{}"
        parsed = json.loads(raw)
        return CandidateProfileData.model_validate(parsed)
    except Exception:
        return None


def extract_candidate_profile(text: str) -> tuple[CandidateProfileData, str]:
    ai_profile = _openai_profile(text)
    if ai_profile is not None:
        ai_profile.skills = _dedupe(ai_profile.skills, limit=40)
        for item in ai_profile.experience:
            item.highlights = _dedupe(item.highlights, limit=20)
            item.skills = _dedupe(item.skills, limit=20)
        return ai_profile, "openai"
    return _fallback_profile(text), "fallback"


@router.get("", response_model=CandidateProfileResponse | None)
async def get_candidate_profile(
    authorization: str | None = Header(None),
) -> CandidateProfileResponse | None:
    user = await verify_supabase_user(authorization)
    result = _db().table("candidate_profiles").select("*").eq("user_id", user["id"]).execute()
    rows = getattr(result, "data", None) or []
    return CandidateProfileResponse(**rows[0]) if rows else None


@router.post("/cv-upload", response_model=CandidateProfileResponse)
async def upload_candidate_cv(
    file: UploadFile = File(...),
    authorization: str | None = Header(None),
) -> CandidateProfileResponse:
    user = await verify_supabase_user(authorization)
    filename = Path(file.filename or "cv").name
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=415, detail="Upload a PDF, DOCX or TXT CV.")

    data = await file.read(MAX_CV_BYTES + 1)
    if len(data) > MAX_CV_BYTES:
        raise HTTPException(status_code=413, detail="CV files must be 5 MB or smaller.")

    text = _extract_text(filename, data)
    profile, provider = extract_candidate_profile(text)
    payload = {
        "user_id": user["id"],
        "source_filename": filename[:255],
        "summary": profile.summary,
        "skills": profile.skills,
        "experience": [item.model_dump() for item in profile.experience],
        "qualifications": [item.model_dump() for item in profile.qualifications],
        "extraction_provider": provider,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    result = _db().table("candidate_profiles").upsert(payload, on_conflict="user_id").execute()
    rows = getattr(result, "data", None) or []
    if not rows:
        raise HTTPException(status_code=503, detail="Could not save the extracted CV profile.")
    return CandidateProfileResponse(**rows[0])


@router.delete("")
async def delete_candidate_profile(
    authorization: str | None = Header(None),
) -> dict[str, bool]:
    user = await verify_supabase_user(authorization)
    _db().table("candidate_profiles").delete().eq("user_id", user["id"]).execute()
    return {"ok": True}
