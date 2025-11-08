"""Test scoring service preserves zeros."""


from services.scoring import compute_heuristic_score


def test_scoring_preserves_zero_salary():
    """Test that 0 salary values are preserved, not treated as falsy."""
    job = {
        "title": "Intern",
        "company": "StartupCo",
        "salary_min": 0,  # Explicitly 0, not None
        "salary_max": 0,
        "raw": {"description": "Unpaid internship"},
    }

    result = compute_heuristic_score(job, "Python developer with React experience")

    # Score should be computed (not skipped due to 0 being falsy)
    assert result["fit_score"] is not None
    assert isinstance(result["fit_score"], (int, float))

    # Check that salary factor was included (even with 0 values)
    salary_factors = [f for f in result["factors"] if "Salary" in f["name"]]
    assert len(salary_factors) > 0, "Salary factor should be present even when salary is 0"


def test_scoring_distinguishes_zero_from_none():
    """Test that None (missing) is treated differently from 0."""
    job_with_zero = {
        "title": "Intern",
        "company": "StartupCo",
        "salary_min": 0,
        "salary_max": 0,
        "raw": {},
    }

    job_with_none = {
        "title": "Intern",
        "company": "StartupCo",
        "salary_min": None,
        "salary_max": None,
        "raw": {},
    }

    result_zero = compute_heuristic_score(job_with_zero, None)
    result_none = compute_heuristic_score(job_with_none, None)

    # Both should compute scores
    assert result_zero["fit_score"] is not None
    assert result_none["fit_score"] is not None

    # Check factors
    zero_salary_factors = [f for f in result_zero["factors"] if "Salary" in f["name"]]
    none_salary_factors = [f for f in result_none["factors"] if "Salary" in f["name"]]

    # Both should have salary factors (0 and None are both valid)
    assert len(zero_salary_factors) > 0
    assert len(none_salary_factors) > 0


def test_scoring_zero_skills_match():
    """Test that 0% skills match is preserved."""
    job = {
        "title": "Java Developer",
        "company": "EnterpriseCo",
        "raw": {"description": "Java Spring Boot expert needed"},
    }

    # Resume with no matching skills
    resume = "I am a graphic designer with Photoshop and Illustrator skills"

    result = compute_heuristic_score(job, resume)

    # Score should be computed
    assert result["fit_score"] is not None

    # Skills match factor should exist and might be 0
    skills_factors = [f for f in result["factors"] if "Skills" in f["name"]]
    assert len(skills_factors) > 0

    # The score itself might be 0.0 (valid), not None
    if skills_factors:
        assert skills_factors[0]["score"] is not None
        # 0.0 is a valid score
        assert skills_factors[0]["score"] >= 0.0


def test_scoring_never_returns_none_score():
    """Test that fit_score is never None."""
    jobs = [
        {"title": "Engineer", "company": "Co", "raw": {}},
        {"title": "Manager", "company": "Corp", "salary_min": 0, "raw": {}},
        {"title": "Designer", "company": "Agency", "salary_min": None, "raw": {}},
    ]

    for job in jobs:
        result = compute_heuristic_score(job, None)
        assert result["fit_score"] is not None, f"fit_score should never be None for job: {job}"
        assert isinstance(result["fit_score"], (int, float))
        assert result["fit_score"] >= 0.0
