"""Saved jobs routes for JobSleuth AI."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

from lib.auth import require_auth
from lib.supabase import supabase

router = APIRouter(prefix="/saved-jobs", tags=["saved"])


class SaveJobRequest(BaseModel):
    """Request body for saving a job."""
    job_id: str


@router.post("/save-job")
async def save_job(
    request: SaveJobRequest,
    authorization: str = Header(...),
):
    """Save a job for the current user."""
    try:
        token = require_auth(authorization)
        
        # Get user from token
        auth_response = supabase.auth.get_user(token)
        if not auth_response or not hasattr(auth_response, 'user') or not auth_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = auth_response.user.id
        
        # Insert saved job (RLS will enforce user_id match)
        response = supabase.table("saved_jobs").insert({
            "user_id": user_id,
            "job_id": request.job_id,
        }).execute()
        
        return {"ok": True, "data": response.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save job: {str(e)}")


@router.get("")
async def get_saved_jobs(
    authorization: str = Header(...),
):
    """Get all saved jobs for the current user."""
    try:
        token = require_auth(authorization)
        
        # Get user from token
        auth_response = supabase.auth.get_user(token)
        if not auth_response or not hasattr(auth_response, 'user') or not auth_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = auth_response.user.id
        
        # Get saved jobs with job details (RLS enforces user_id)
        response = supabase.table("saved_jobs")\
            .select("*, jobs(*)")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()
        
        return {"jobs": response.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch saved jobs: {str(e)}")
