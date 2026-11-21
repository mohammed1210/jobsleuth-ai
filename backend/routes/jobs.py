"""Read real job postings from the public-read Supabase jobs table.

Unlike the old MVP demo, no fictional job rows are returned when the database
is empty or unavailable. The jobs table is SELECT-granted to the anon key with
a public-read RLS policy in the isolated Supabase project.
"""

from __future__ import annotations

import re
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from lib.supabase import get_supabase_anon_client

router = APIRouter(prefix="/jobs", tags=["jobs"])

PUBLIC_FIELDS = (
    "id,title,company,location,salary,salary_min,salary_max,"
    "role_type,source,url,description,created_at"
)
# This raw value is embedded in PostgREST's or_() filter grammar; reject
# control, filter and wildcard punctuation rather than allow filter injection.
SAFE_SEARCH_RE = re.compile(r"^[^\W_]+(?:[ -]+[^\W_]+)*$", flags=re.UNICODE)


class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    location: str
    salary: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    role_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    ai_score: Optional[float] = None
    date_posted: Optional[str] = None
    description: Optional[str] = None


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int
    page: int
    per_page: int


def _safe_search(text: str | None, label: str) -> str | None:
    if text is None:
        return None
    value = text.strip()
    if not value:
        return None
    if not SAFE_SEARCH_RE.fullmatch(value):
        raise HTTPException(
            status_code=422,
            detail=f"{label} contains unsupported search characters",
        )
    return value


def _record(row: dict) -> JobResponse:
    try:
        return JobResponse(
            **{key: value for key, value in row.items() if key != "created_at"},
            # This is the insertion time, not necessarily the advertiser's
            # publication date: do not claim an external job-posting timestamp.
            date_posted=None,
            ai_score=None,
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Job data unavailable") from exc


@router.get("", response_model=JobListResponse)
async def list_jobs(
    q: Optional[str] = Query(None, max_length=120, description="Job title or company"),
    location: Optional[str] = Query(None, max_length=120),
    role_type: Optional[str] = Query(None, max_length=120),
    salary_min: Optional[int] = Query(None, ge=0),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
) -> JobListResponse:
    search = _safe_search(q, "Job search")
    place = _safe_search(location, "Location")
    kind = _safe_search(role_type, "Role type")
    start = (page - 1) * per_page
    end = start + per_page - 1

    try:
        query = get_supabase_anon_client().table("jobs").select(
            PUBLIC_FIELDS, count="exact"
        )
        if search:
            # Escaping is enforced by SAFE_SEARCH_RE: no commas, parentheses,
            # quote marks, periods, or LIKE wildcards can enter this expression.
            query = query.or_(
                f"title.ilike.%{search}%,company.ilike.%{search}%"
            )
        if place:
            query = query.ilike("location", f"%{place}%")
        if kind:
            query = query.ilike("role_type", kind)
        if salary_min is not None:
            # Unknown salary maxima are excluded from a minimum-salary filter.
            query = query.gte("salary_max", salary_min)
        response = query.order("created_at", desc=True).order("id", desc=True).range(start, end).execute()
        if response.count is None or response.data is None:
            raise HTTPException(status_code=503, detail="Job data unavailable")
        return JobListResponse(
            jobs=[_record(row) for row in response.data],
            total=response.count,
            page=page,
            per_page=per_page,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Job data unavailable") from exc


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int) -> JobResponse:
    if job_id < 1:
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        response = (
            get_supabase_anon_client().table("jobs").select(PUBLIC_FIELDS)
            .eq("id", job_id).limit(1).execute()
        )
        if response.data is None:
            raise HTTPException(status_code=503, detail="Job data unavailable")
        if not response.data:
            raise HTTPException(status_code=404, detail="Job not found")
        return _record(response.data[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Job data unavailable") from exc
