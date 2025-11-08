"""Test jobs list and detail endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from main import app

client = TestClient(app)


@patch("routes.jobs.supabase_admin")
def test_list_jobs(mock_supabase):
    """Test listing jobs with pagination."""
    # Mock response
    mock_response = Mock()
    mock_response.data = [
        {
            "id": "test-id-1",
            "title": "Software Engineer",
            "company": "TechCorp",
            "location": "San Francisco",
            "salary_min": 100000,
            "salary_max": 150000,
        }
    ]
    mock_response.count = 1
    
    mock_query = Mock()
    mock_query.execute.return_value = mock_response
    mock_query.order.return_value = mock_query
    mock_query.range.return_value = mock_query
    
    mock_table = Mock()
    mock_table.select.return_value = mock_query
    mock_supabase.table.return_value = mock_table
    
    response = client.get("/jobs?page=1&per_page=20")
    
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert "total" in data
    assert "page" in data
    assert data["page"] == 1


@patch("routes.jobs.supabase_admin")
def test_get_job_detail(mock_supabase):
    """Test getting a specific job by ID."""
    # Mock response
    mock_response = Mock()
    mock_response.data = [
        {
            "id": "test-id-1",
            "title": "Software Engineer",
            "company": "TechCorp",
        }
    ]
    
    mock_query = Mock()
    mock_query.execute.return_value = mock_response
    mock_query.eq.return_value = mock_query
    
    mock_table = Mock()
    mock_table.select.return_value = mock_query
    mock_supabase.table.return_value = mock_table
    
    job_id = "550e8400-e29b-41d4-a716-446655440000"
    response = client.get(f"/jobs/{job_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Software Engineer"


@patch("routes.jobs.supabase_admin")
def test_get_job_not_found(mock_supabase):
    """Test 404 when job doesn't exist."""
    # Mock empty response
    mock_response = Mock()
    mock_response.data = []
    
    mock_query = Mock()
    mock_query.execute.return_value = mock_response
    mock_query.eq.return_value = mock_query
    
    mock_table = Mock()
    mock_table.select.return_value = mock_query
    mock_supabase.table.return_value = mock_table
    
    job_id = "550e8400-e29b-41d4-a716-446655440000"
    response = client.get(f"/jobs/{job_id}")
    
    assert response.status_code == 404
