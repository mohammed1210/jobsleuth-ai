"""
Job scoring API routes.

Endpoints for AI-powered job fit scoring.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.scoring import score_job


router = APIRouter(tags=["scoring"])


class ScoreRequest(BaseModel):
    """Request body for job scoring."""
    job: Dict[str, Any]
    resumeText: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


@router.post("/score")
async def score_job_endpoint(request: ScoreRequest) -> Dict[str, Any]:
    """
    Compute AI fit score for a job.
    
    Args:
        request: Score request with job details, optional resume and preferences
        
    Returns:
        Scoring result with fit_score (0-100) and factors
    """
    try:
        result = await score_job(
            job=request.job,
            resume_text=request.resumeText,
            preferences=request.preferences,
            use_ai=True
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")
