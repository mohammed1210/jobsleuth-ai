"""Jobs routes for JobSleuth AI."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from lib.supabase import supabase_admin

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("")
async def list_jobs(
    q: str | None = Query(None, description="Search query"),
    location: str | None = Query(None, description="Location filter"),
    minSalary: int | None = Query(None, description="Minimum salary"),  # noqa: N803
    type: str | None = Query(None, description="Job type"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """List jobs with optional filters and pagination."""
    try:
        # Build query
        query = supabase_admin.table("jobs").select("*", count="exact")

        # Apply filters
        if q:
            query = query.or_(f"title.ilike.%{q}%,company.ilike.%{q}%")

        if location:
            query = query.ilike("location", f"%{location}%")

        if minSalary:
            query = query.gte("salary_min", minSalary)

        if type:
            query = query.eq("type", type)

        # Apply pagination
        offset = (page - 1) * per_page
        query = query.order("created_at", desc=True).range(offset, offset + per_page - 1)

        # Execute query
        response = query.execute()

        total = response.count if hasattr(response, "count") else len(response.data)

        return {
            "jobs": response.data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page if total else 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch jobs: {str(e)}")


@router.get("/{job_id}")
async def get_job(job_id: UUID):
    """Get a specific job by ID."""
    try:
        response = supabase_admin.table("jobs").select("*").eq("id", str(job_id)).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Job not found")

        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch job: {str(e)}")
