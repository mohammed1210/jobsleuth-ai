"""Extract structured criteria from user-supplied vacancy text."""

from __future__ import annotations

import json
import re
from typing import Any, Literal

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from lib.settings import settings
from routes.saved_jobs import verify_supabase_user
from routes.vacancy_analysis import Requirement

router = APIRouter(prefix="/vacancy-analysis", tags=["vacancy_analysis"])


class VacancyExtractRequest(BaseModel):
    vacancy_text: str = Field(min_length=20, max_length=50000)


def _clean(value: str) -> str:
    return re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", value).strip()


def _blocker(text: str) -> bool:
    lowered = text.lower()
    cues = (
        "right to work",
        "security clearance",
        "driving licence",
        "professional registration",
        "required qualification",
        "nationality requirement",
        "citizenship requirement",
    )
    return any(cue in lowered for cue in cues)


def fallback_extract(text: str) -> tuple[list[Requirement], list[str]]:
    requirements: list[Requirement] = []
    practical: list[str] = []
    section: Literal["essential", "desirable", "practical"] = "essential"

    for raw in text.splitlines():
        line = _clean(raw)
        if not line:
            continue
        lowered = line.lower().rstrip(":")

        if len(line) <= 90:
            if "desirable" in lowered or "nice to have" in lowered:
                section = "desirable"
                continue
            if any(cue in lowered for cue in ("essential criteria", "essential requirements", "person specification", "what you will need", "what you'll need")):
                section = "essential"
                continue
            if any(cue in lowered for cue in ("working pattern", "working arrangements", "hours", "location", "travel requirements")):
                section = "practical"
                continue

        if section == "practical":
            practical.append(line)
            continue

        if any(cue in lowered for cue in ("training will be provided", "training is provided", "full training provided", "we will train")):
            requirements.append(Requirement(text=line, category="trainable"))
            continue

        practical_cues = ("hours per week", "days per week", "office attendance", "hybrid working", "shift pattern", "weekend working", "travel required", "full-time", "part-time")
        if any(cue in lowered for cue in practical_cues):
            practical.append(line)
            continue

        requirement_cues = ("experience", "knowledge", "ability to", "able to", "skill", "must", "required", "essential", "desirable", "ideally", "qualification")
        if not (raw.lstrip().startswith(("-", "*", "•")) or any(cue in lowered for cue in requirement_cues)):
            continue
        if len(line) > 350:
            continue

        category: Literal["essential", "desirable", "trainable"] = "desirable" if section == "desirable" else "essential"
        if "desirable" in lowered or "ideally" in lowered or "advantage" in lowered:
            category = "desirable"
        requirements.append(Requirement(text=line, category=category, blocker=_blocker(line)))

    unique: list[Requirement] = []
    seen = set()
    for item in requirements:
        key = item.text.lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique[:24], list(dict.fromkeys(practical))[:10]


def openai_extract(text: str) -> tuple[list[Requirement], list[str]]:
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "Extract only criteria supported by the vacancy. Return JSON with requirements and practical_issues. Each requirement needs text, category essential/desirable/trainable, and blocker. Use blocker only for explicit eligibility or credential conditions. Practical issues include hours, working pattern, location, travel, shifts, office attendance, or mandatory training. Do not invent criteria."},
            {"role": "user", "content": f"Vacancy text:\n{text}"},
        ],
        temperature=0,
        max_tokens=1400,
    )
    payload = json.loads(response.choices[0].message.content or "{}")
    requirements = [Requirement(**item) for item in payload.get("requirements", []) if isinstance(item, dict) and item.get("text")]
    practical = [str(item).strip() for item in payload.get("practical_issues", []) if str(item).strip()]
    if not requirements and not practical:
        raise ValueError("No structured vacancy data")
    return requirements[:24], practical[:10]


@router.post("/extract")
async def extract_vacancy(request: VacancyExtractRequest, authorization: str | None = Header(None)) -> dict[str, Any]:
    await verify_supabase_user(authorization)
    if settings.OPENAI_API_KEY:
        try:
            requirements, practical = openai_extract(request.vacancy_text)
            return {"ok": True, "provider": "openai", "requirements": requirements, "practical_issues": practical}
        except Exception:
            pass

    requirements, practical = fallback_extract(request.vacancy_text)
    return {"ok": True, "provider": "fallback", "requirements": requirements, "practical_issues": practical}
