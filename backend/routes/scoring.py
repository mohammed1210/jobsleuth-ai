"""Scoring routes for JobSleuth AI."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.scoring import compute_ai_score

router = APIRouter(prefix="/score", tags=["scoring"])


class ScoreRequest(BaseModel):
    """Request body for job scoring."""
    job: Dict[str, Any]
    resumeText: Optional[str] = None


@router.post("")
async def score_job(request: ScoreRequest):
    """Compute job fit score for a job and optional resume.
    
    Returns fit_score (0-100) and factors array.
    Uses OpenAI if OPENAI_API_KEY is present, otherwise uses heuristic scoring.
    """
    try:
        result = await compute_ai_score(request.job, request.resumeText)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute score: {str(e)}")
