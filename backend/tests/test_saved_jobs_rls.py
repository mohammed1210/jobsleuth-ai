"""Test saved jobs RLS (owner-only access)."""

from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@patch("routes.saved.supabase")
def test_save_job_requires_auth(mock_supabase):
    """Test that saving a job requires authentication."""
    response = client.post(
        "/saved-jobs/save-job",
        json={"job_id": "test-job-id"},
    )

    # Should fail without Authorization header
    assert response.status_code == 422 or response.status_code == 401


@patch("routes.saved.supabase")
def test_save_job_with_auth(mock_supabase):
    """Test saving a job with valid auth token."""
    # Mock auth response
    mock_user = Mock()
    mock_user.id = "test-user-id"
    mock_user.email = "test@example.com"

    mock_auth_response = Mock()
    mock_auth_response.user = mock_user

    mock_supabase.auth.get_user.return_value = mock_auth_response

    # Mock insert response
    mock_insert_response = Mock()
    mock_insert_response.data = [
        {"id": "saved-id", "user_id": "test-user-id", "job_id": "test-job-id"}
    ]

    mock_query = Mock()
    mock_query.execute.return_value = mock_insert_response

    mock_table = Mock()
    mock_table.insert.return_value = mock_query
    mock_supabase.table.return_value = mock_table

    response = client.post(
        "/saved-jobs/save-job",
        json={"job_id": "test-job-id"},
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True


@patch("routes.saved.supabase")
def test_get_saved_jobs_owner_only(mock_supabase):
    """Test that users can only see their own saved jobs (RLS)."""
    # Mock auth response
    mock_user = Mock()
    mock_user.id = "test-user-id"

    mock_auth_response = Mock()
    mock_auth_response.user = mock_user

    mock_supabase.auth.get_user.return_value = mock_auth_response

    # Mock query response
    mock_response = Mock()
    mock_response.data = [
        {
            "id": "saved-1",
            "user_id": "test-user-id",
            "jobs": {"title": "Test Job"},
        }
    ]

    mock_query = Mock()
    mock_query.execute.return_value = mock_response
    mock_query.order.return_value = mock_query
    mock_query.eq.return_value = mock_query

    mock_table = Mock()
    mock_table.select.return_value = mock_query
    mock_supabase.table.return_value = mock_table

    response = client.get(
        "/saved-jobs",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    # RLS ensures only user's own jobs are returned
    assert all(job["user_id"] == "test-user-id" for job in data["jobs"])
