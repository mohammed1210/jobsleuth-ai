"""Job listing routes for JobSleuth AI backend."""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobResponse(BaseModel):
    """Job response model."""
    id: int
    title: str
    company: str
    location: str
    salary: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    date_posted: Optional[str] = None
    description: Optional[str] = None


class JobListResponse(BaseModel):
    """Job list response model."""
    jobs: list[JobResponse]
    total: int
    page: int
    per_page: int


@router.get("", response_model=JobListResponse)
async def list_jobs(
    q: Optional[str] = Query(None, description="Search query"),
    location: Optional[str] = Query(None, description="Location filter"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Results per page"),
) -> JobListResponse:
    """List jobs with optional filters and pagination.
    
    Args:
        q: Search query
        location: Location filter
        page: Page number (starting from 1)
        per_page: Results per page
        
    Returns:
        Paginated list of jobs
    """
    # Mock data for now - will be replaced with actual database queries
    mock_jobs = [
        JobResponse(
            id=1,
            title="Senior Software Engineer",
            company="TechCorp",
            location="San Francisco, CA",
            salary="$120k - $180k",
            source="Indeed",
            date_posted="2 days ago",
            url="https://example.com/job/1",
            description="We are seeking a talented Senior Software Engineer...",
        ),
        JobResponse(
            id=2,
            title="Frontend Developer",
            company="StartupXYZ",
            location="Remote",
            salary="$90k - $130k",
            source="LinkedIn",
            date_posted="1 week ago",
            url="https://example.com/job/2",
            description="Join our team as a Frontend Developer...",
        ),
        JobResponse(
            id=3,
            title="Full Stack Engineer",
            company="BigTech Inc",
            location="New York, NY",
            salary="$100k - $150k",
            source="Indeed",
            date_posted="3 days ago",
            url="https://example.com/job/3",
            description="We're looking for a Full Stack Engineer...",
        ),
    ]
    
    # Apply filters (mock implementation)
    filtered_jobs = mock_jobs
    if q:
        q_lower = q.lower()
        filtered_jobs = [
            job for job in filtered_jobs
            if q_lower in job.title.lower() or q_lower in job.company.lower()
        ]
    
    if location:
        location_lower = location.lower()
        filtered_jobs = [
            job for job in filtered_jobs
            if location_lower in job.location.lower()
        ]
    
    # Pagination
    total = len(filtered_jobs)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_jobs = filtered_jobs[start:end]
    
    return JobListResponse(
        jobs=paginated_jobs,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int) -> JobResponse:
    """Get a single job by ID.
    
    Args:
        job_id: Job ID
        
    Returns:
        Job details
        
    Raises:
        HTTPException: If job not found
    """
    # Mock data for now
    mock_jobs = {
        1: JobResponse(
            id=1,
            title="Senior Software Engineer",
            company="TechCorp",
            location="San Francisco, CA",
            salary="$120k - $180k",
            source="Indeed",
            date_posted="2 days ago",
            url="https://example.com/job/1",
            description="""
                <h3>About the Role</h3>
                <p>We are seeking a talented Senior Software Engineer to join our growing team.</p>
                <h3>Responsibilities</h3>
                <ul>
                    <li>Design and develop scalable web applications</li>
                    <li>Collaborate with cross-functional teams</li>
                    <li>Write clean, maintainable code</li>
                </ul>
            """,
        ),
        2: JobResponse(
            id=2,
            title="Frontend Developer",
            company="StartupXYZ",
            location="Remote",
            salary="$90k - $130k",
            source="LinkedIn",
            date_posted="1 week ago",
            url="https://example.com/job/2",
            description="<p>Join our team as a Frontend Developer...</p>",
        ),
    }
    
    job = mock_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job
