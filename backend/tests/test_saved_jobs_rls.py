"""Tests for saved jobs with Row Level Security (owner-only access)."""

import pytest
from fastapi.testclient import TestClient


# This will be imported once routes are created
# from backend.main import app
# client = TestClient(app)


def test_user_can_save_job():
    """Test that authenticated user can save a job."""
    # TODO: Implement once saved jobs routes are created
    pass


def test_user_can_view_own_saved_jobs():
    """Test that user can view their own saved jobs."""
    # TODO: Implement once saved jobs routes are created
    pass


def test_user_cannot_view_others_saved_jobs():
    """Test RLS: user cannot view another user's saved jobs."""
    # TODO: Implement once saved jobs routes are created
    pass


def test_unauthenticated_cannot_save_jobs():
    """Test that unauthenticated users cannot save jobs."""
    # TODO: Implement once saved jobs routes are created
    pass
