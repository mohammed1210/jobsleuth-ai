"""Test saved jobs with RLS (Row Level Security)."""

import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


def test_save_job_requires_auth():
    """Test that saving a job requires authentication."""
    response = client.post("/save-job", json={"job_id": "some-uuid"})
    assert response.status_code == 401


def test_get_saved_jobs_requires_auth():
    """Test that getting saved jobs requires authentication."""
    response = client.get("/saved-jobs")
    assert response.status_code == 401


def test_delete_saved_job_requires_auth():
    """Test that deleting saved job requires authentication."""
    response = client.delete("/saved-jobs/some-uuid")
    assert response.status_code == 401


def test_save_job_with_invalid_job_id():
    """Test saving job with non-existent job ID fails (with auth)."""
    # This would require a valid JWT token
    # For now, we test that the endpoint exists and requires proper auth
    fake_token = "Bearer fake-token"
    response = client.post(
        "/save-job",
        json={"job_id": "00000000-0000-0000-0000-000000000000"},
        headers={"Authorization": fake_token}
    )
    # Should fail due to invalid token or missing user
    assert response.status_code in [401, 403, 404]


# Note: Full RLS testing requires:
# 1. A test Supabase instance or mock
# 2. Valid JWT tokens for different users
# 3. Verification that users can only access their own saved jobs
# These tests serve as placeholders for the RLS behavior verification
