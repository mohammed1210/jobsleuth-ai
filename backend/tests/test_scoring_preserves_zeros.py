"""Test scoring service to ensure it preserves zeros."""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.scoring import (
    compute_salary_score,
    compute_heuristic_score,
)


def test_salary_score_with_zero_values():
    """Test that salary scoring doesn't treat 0 as falsy."""
    # Case 1: salary is 0 (valid value, not None)
    score = compute_salary_score(job_salary_min=0, job_salary_max=0, desired_salary=50000)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    # Should return a low score, not neutral 0.5
    assert score < 0.5
    
    # Case 2: salary is None (should return neutral)
    score_none = compute_salary_score(job_salary_min=None, job_salary_max=None, desired_salary=50000)
    assert score_none == 0.5


def test_salary_score_preserves_zero_salary():
    """Test that zero salary is properly handled and not confused with None."""
    # Unpaid internship or volunteer position (salary = 0)
    score = compute_salary_score(job_salary_min=0, job_salary_max=0, desired_salary=100000)
    
    # Should get a very low score (close to 0)
    assert 0.0 <= score < 0.1
    
    # Should not be neutral (0.5)
    assert score != 0.5


def test_salary_score_with_desired_zero():
    """Test salary scoring when desired salary is 0."""
    # Edge case: user desires unpaid work
    score = compute_salary_score(job_salary_min=0, job_salary_max=0, desired_salary=0)
    
    # Should handle gracefully (avoid division by zero)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


@pytest.mark.asyncio
async def test_heuristic_score_preserves_zero_salary():
    """Test that heuristic scoring preserves zero salary values."""
    job = {
        "title": "Software Engineer",
        "company": "TechCorp",
        "location": "Remote",
        "salary_min": 0,  # Explicitly 0, not None
        "salary_max": 0,
        "raw": {"description": "Great opportunity"}
    }
    
    preferences = {
        "salary": 100000,
        "locations": ["Remote"],
        "years_experience": 3
    }
    
    result = await compute_heuristic_score(job, resume_text="Python developer", preferences=preferences)
    
    assert "fit_score" in result
    assert "factors" in result
    
    # Find salary factor
    salary_factor = next((f for f in result["factors"] if f["name"] == "Salary Fit"), None)
    assert salary_factor is not None
    
    # Salary score should be low (not neutral 50)
    assert salary_factor["score"] < 30


@pytest.mark.asyncio
async def test_heuristic_score_with_none_salary():
    """Test that None salary returns neutral score."""
    job = {
        "title": "Software Engineer",
        "company": "TechCorp",
        "location": "Remote",
        "salary_min": None,  # Not specified
        "salary_max": None,
        "raw": {"description": "Great opportunity"}
    }
    
    preferences = {
        "salary": 100000,
        "locations": ["Remote"],
        "years_experience": 3
    }
    
    result = await compute_heuristic_score(job, resume_text="Python developer", preferences=preferences)
    
    # Find salary factor
    salary_factor = next((f for f in result["factors"] if f["name"] == "Salary Fit"), None)
    assert salary_factor is not None
    
    # Should be neutral (50) when salary is None
    assert salary_factor["score"] == 50.0
