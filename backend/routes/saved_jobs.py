"""Saved jobs routes for JobSleuth AI backend with RLS."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel

router = APIRouter(prefix="/saved", tags=["saved_jobs"])


class SavedJobRequest(BaseModel):
    """Request to save a job."""
    job_id: int


class SavedJobResponse(BaseModel):
    """Saved job response."""
    id: int
    user_id: str
    job_id: int
    saved_at: str


def verify_token(authorization: Optional[str]) -> str:
    """Verify bearer token and return user ID.
    
    Args:
        authorization: Authorization header
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    # Mock validation - in production, validate with Supabase
    if not token or token == "invalid":
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Return mock user ID - in production, decode JWT and get user ID
    return "user_123"


@router.post("", response_model=SavedJobResponse)
async def save_job(
    request: SavedJobRequest,
    authorization: Optional[str] = Header(None)
) -> SavedJobResponse:
    """Save a job for the authenticated user.
    
    Args:
        request: Save job request
        authorization: Bearer token
        
    Returns:
        Saved job details
        
    Raises:
        HTTPException: If unauthorized
    """
    user_id = verify_token(authorization)
    
    # Mock implementation - in production, insert into database
    return SavedJobResponse(
        id=1,
        user_id=user_id,
        job_id=request.job_id,
        saved_at="2024-01-15T10:30:00Z",
    )


@router.get("", response_model=list[SavedJobResponse])
async def list_saved_jobs(
    authorization: Optional[str] = Header(None)
) -> list[SavedJobResponse]:
    """List saved jobs for the authenticated user (RLS enforced).
    
    Args:
        authorization: Bearer token
        
    Returns:
        List of saved jobs (only for the authenticated user)
        
    Raises:
        HTTPException: If unauthorized
    """
    user_id = verify_token(authorization)
    
    # Mock implementation - in production, query database with RLS
    # The database should enforce that users can only see their own saved jobs
    mock_saved_jobs = [
        SavedJobResponse(
            id=1,
            user_id=user_id,
            job_id=1,
            saved_at="2024-01-15T10:30:00Z",
        ),
        SavedJobResponse(
            id=2,
            user_id=user_id,
            job_id=2,
            saved_at="2024-01-14T15:20:00Z",
        ),
    ]
    
    return mock_saved_jobs


@router.delete("/{saved_job_id}")
async def unsave_job(
    saved_job_id: int,
    authorization: Optional[str] = Header(None)
) -> dict:
    """Remove a saved job (RLS enforced - user can only delete their own).
    
    Args:
        saved_job_id: Saved job ID
        authorization: Bearer token
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If unauthorized or not found
    """
    user_id = verify_token(authorization)
    
    # Mock implementation - in production, delete from database with RLS check
    # The database should enforce that users can only delete their own saved jobs
    
    return {"status": "success", "message": "Job unsaved"}
