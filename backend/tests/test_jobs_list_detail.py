"""Test jobs list and detail endpoints."""

from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


def test_list_jobs_endpoint():
    """Test that jobs list endpoint returns paginated results."""
    response = client.get("/jobs?page=1&per_page=10")
    assert response.status_code == 200
    
    data = response.json()
    assert "jobs" in data
    assert "pagination" in data
    
    pagination = data["pagination"]
    assert pagination["page"] == 1
    assert pagination["per_page"] == 10
    assert "total" in pagination
    assert "total_pages" in pagination
    assert "has_next" in pagination
    assert "has_prev" in pagination


def test_list_jobs_with_search():
    """Test jobs search with query parameter."""
    response = client.get("/jobs?q=engineer")
    assert response.status_code == 200
    
    data = response.json()
    assert "jobs" in data
    # Results should be filtered but we can't assert exact count without knowing DB state


def test_list_jobs_with_location_filter():
    """Test jobs filter by location."""
    response = client.get("/jobs?location=Remote")
    assert response.status_code == 200
    
    data = response.json()
    assert "jobs" in data


def test_list_jobs_with_salary_filter():
    """Test jobs filter by minimum salary."""
    response = client.get("/jobs?minSalary=100000")
    assert response.status_code == 200
    
    data = response.json()
    assert "jobs" in data


def test_list_jobs_with_type_filter():
    """Test jobs filter by type."""
    response = client.get("/jobs?type=Full-time")
    assert response.status_code == 200
    
    data = response.json()
    assert "jobs" in data


def test_get_job_detail_not_found():
    """Test job detail with non-existent ID returns 404."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/jobs/{fake_uuid}")
    assert response.status_code == 404
    
    data = response.json()
    assert "detail" in data
