"""
Jobs API routes.

Endpoints for searching and viewing job listings.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query

from backend.lib.supabase import execute_query, get_supabase_client


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("")
async def list_jobs(
    q: Optional[str] = Query(None, description="Search query"),
    location: Optional[str] = Query(None, description="Location filter"),
    minSalary: Optional[int] = Query(None, description="Minimum salary"),
    type: Optional[str] = Query(None, description="Job type (Full-time, Part-time, etc.)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page")
) -> Dict[str, Any]:
    """
    List and search jobs with pagination and filters.
    
    Returns:
        Dictionary with jobs list, pagination info, and total count
    """
    client = get_supabase_client()
    query_builder = client.table("jobs").select("*", count="exact")
    
    # Apply search filter on title and company
    if q:
        query_builder = query_builder.or_(f"title.ilike.%{q}%,company.ilike.%{q}%")
    
    # Apply location filter
    if location:
        query_builder = query_builder.ilike("location", f"%{location}%")
    
    # Apply salary filter
    if minSalary is not None:
        query_builder = query_builder.or_(
            f"salary_min.gte.{minSalary},salary_max.gte.{minSalary}"
        )
    
    # Apply type filter
    if type:
        query_builder = query_builder.eq("type", type)
    
    # Apply pagination
    offset = (page - 1) * per_page
    query_builder = query_builder.order("posted_at", desc=True).range(offset, offset + per_page - 1)
    
    # Execute query
    result = query_builder.execute()
    
    total = result.count if result.count is not None else 0
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    
    return {
        "jobs": result.data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


@router.get("/{job_id}")
async def get_job(job_id: str) -> Dict[str, Any]:
    """
    Get a single job by ID.
    
    Args:
        job_id: Job UUID
        
    Returns:
        Job dictionary
        
    Raises:
        HTTPException: If job not found
    """
    client = get_supabase_client()
    result = client.table("jobs").select("*").eq("id", job_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return result.data[0]
