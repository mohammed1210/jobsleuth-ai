"""
Saved jobs API routes.

Endpoints for saving and managing saved jobs (user bookmarks).
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from backend.lib.auth import require_auth
from backend.lib.supabase import get_supabase_client


router = APIRouter(tags=["saved"])


class SaveJobRequest(BaseModel):
    """Request body for saving a job."""
    job_id: str


@router.post("/save-job")
async def save_job(
    request: SaveJobRequest,
    user_id: str = Depends(require_auth)
) -> Dict[str, Any]:
    """
    Save a job for the current user.
    
    Args:
        request: Save job request with job_id
        user_id: Current user ID from auth token
        
    Returns:
        Success message and saved job record
    """
    client = get_supabase_client()
    
    # Check if job exists
    job_result = client.table("jobs").select("id").eq("id", request.job_id).execute()
    if not job_result.data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if already saved
    existing = client.table("saved_jobs").select("id").eq("user_id", user_id).eq("job_id", request.job_id).execute()
    if existing.data:
        return {
            "message": "Job already saved",
            "saved_job": existing.data[0]
        }
    
    # Save the job
    result = client.table("saved_jobs").insert({
        "user_id": user_id,
        "job_id": request.job_id
    }).execute()
    
    return {
        "message": "Job saved successfully",
        "saved_job": result.data[0] if result.data else None
    }


@router.get("/saved-jobs")
async def get_saved_jobs(
    user_id: str = Depends(require_auth)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all saved jobs for the current user.
    
    Args:
        user_id: Current user ID from auth token
        
    Returns:
        Dictionary with list of saved jobs (with job details)
    """
    client = get_supabase_client()
    
    # Get saved jobs with job details via join
    result = client.table("saved_jobs") \
        .select("*, jobs(*)") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .execute()
    
    return {
        "saved_jobs": result.data
    }


@router.delete("/saved-jobs/{saved_job_id}")
async def unsave_job(
    saved_job_id: str,
    user_id: str = Depends(require_auth)
) -> Dict[str, str]:
    """
    Remove a saved job.
    
    Args:
        saved_job_id: Saved job record ID
        user_id: Current user ID from auth token
        
    Returns:
        Success message
    """
    client = get_supabase_client()
    
    # Delete the saved job (RLS ensures user can only delete their own)
    result = client.table("saved_jobs") \
        .delete() \
        .eq("id", saved_job_id) \
        .eq("user_id", user_id) \
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Saved job not found")
    
    return {"message": "Job unsaved successfully"}
