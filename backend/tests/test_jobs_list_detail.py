"""Tests for jobs list and detail endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_list_jobs_endpoint():
    """Test listing jobs with pagination."""
    response = client.get("/jobs")
    assert response.status_code == 200
    
    data = response.json()
    assert "jobs" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data
    assert isinstance(data["jobs"], list)


def test_list_jobs_with_filters():
    """Test jobs list with search filters."""
    response = client.get("/jobs?q=Software&location=San Francisco")
    assert response.status_code == 200
    
    data = response.json()
    assert "jobs" in data
    # Filtered results should be returned
    assert isinstance(data["jobs"], list)


def test_list_jobs_pagination():
    """Test jobs list pagination."""
    response = client.get("/jobs?page=1&per_page=2")
    assert response.status_code == 200
    
    data = response.json()
    assert data["page"] == 1
    assert data["per_page"] == 2


def test_get_job_detail():
    """Test getting a single job by ID."""
    response = client.get("/jobs/1")
    assert response.status_code == 200
    
    job = response.json()
    assert "id" in job
    assert "title" in job
    assert "company" in job
    assert job["id"] == 1


def test_job_detail_not_found():
    """Test 404 response for non-existent job."""
    response = client.get("/jobs/99999")
    assert response.status_code == 404
    
    data = response.json()
    assert "detail" in data
