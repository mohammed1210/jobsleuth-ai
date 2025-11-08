"""Tests for scoring system, ensuring zeros are preserved."""

import pytest
from backend.services.scoring import (
    calculate_skills_overlap,
    calculate_salary_fit,
    calculate_heuristic_score,
)


def test_skills_overlap_with_zero():
    """Test that zero skills overlap is preserved (not treated as falsy)."""
    user_skills = ["Python", "JavaScript"]
    job_skills = ["Java", "C++"]
    
    score = calculate_skills_overlap(user_skills, job_skills)
    
    # Should be 0.0, not None or falsy
    assert score == 0.0
    assert score is not None
    assert isinstance(score, float)


def test_salary_fit_with_zero_salary():
    """Test that zero salary values are handled correctly."""
    # User willing to work for $0 (e.g., volunteer, internship)
    user_min_salary = 0.0
    user_max_salary = 50000.0
    
    # Job offering $0 - $1000
    job_salary_min = 0.0
    job_salary_max = 1000.0
    
    score = calculate_salary_fit(
        user_min_salary,
        user_max_salary,
        job_salary_min,
        job_salary_max
    )
    
    # Should have a positive score since ranges overlap
    assert score > 0.0
    assert isinstance(score, float)


def test_salary_fit_distinguishes_zero_from_none():
    """Test that None and 0 are treated differently for salary."""
    user_min_salary = 0.0  # Explicitly $0
    
    # Job with no salary specified (None)
    score_none = calculate_salary_fit(user_min_salary, None, None, None)
    
    # Job with $0 salary
    score_zero = calculate_salary_fit(user_min_salary, None, 0.0, 0.0)
    
    # Both should be valid floats
    assert isinstance(score_none, float)
    assert isinstance(score_zero, float)
    
    # Score with None should be neutral (0.5)
    assert score_none == 0.5
    
    # Score with 0 should be computed normally
    assert score_zero >= 0.0


def test_heuristic_score_preserves_all_zeros():
    """Test that heuristic scoring preserves zero scores."""
    user_profile = {
        "skills": ["Python", "React"],
        "desired_title": "Software Engineer",
        "location": "New York",
        "min_salary": 100000,
        "max_salary": 150000,
        "seniority_level": "Senior",
        "remote_ok": False,
    }
    
    # Job with no overlap
    job = {
        "title": "Marketing Manager",
        "company": "Test Corp",
        "location": "Los Angeles",
        "required_skills": ["Marketing", "SEO"],
        "salary_min": 60000,
        "salary_max": 80000,
        "seniority_level": "Junior",
    }
    
    scores = calculate_heuristic_score(user_profile, job)
    
    # Should have low scores, including zeros
    assert "skills_score" in scores
    assert "overall_score" in scores
    
    # Verify all scores are floats (including if they're 0.0)
    for key, value in scores.items():
        assert isinstance(value, float), f"{key} should be float, got {type(value)}"
        assert value >= 0.0, f"{key} should be non-negative"
        assert value <= 1.0, f"{key} should not exceed 1.0"
    
    # Skills score should be 0.0 (no overlap)
    assert scores["skills_score"] == 0.0


def test_empty_skills_returns_zero_not_falsy():
    """Test that empty user skills returns 0.0, not falsy value."""
    user_skills = []  # Empty list
    job_skills = ["Python", "Java"]
    
    score = calculate_skills_overlap(user_skills, job_skills)
    
    # Should be exactly 0.0
    assert score == 0.0
    assert score is not None
    assert not (score is False)


def test_none_vs_zero_in_salary():
    """Test explicit distinction between None and 0 in salary calculations."""
    # Case 1: None means "not specified"
    score_none = calculate_salary_fit(None, None, 50000, 100000)
    assert score_none == 0.5  # Neutral
    
    # Case 2: 0 means "$0 minimum" - job range is within user's acceptable range
    score_zero = calculate_salary_fit(0, 100000, 50000, 100000)
    # User accepts 0-100k, job offers 50-100k: overlap is 50k out of 100k = 0.5
    assert score_zero == 0.5
    assert isinstance(score_zero, float)
    
    # Case 3: Job offers $0 (valid) - should have overlap
    score_job_zero = calculate_salary_fit(0, 50000, 0, 10000)
    assert isinstance(score_job_zero, float)
    assert score_job_zero > 0.0  # Should match (10k overlap out of 50k range)
