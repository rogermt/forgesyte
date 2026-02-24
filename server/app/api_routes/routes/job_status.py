"""Job status endpoint: GET /video/status/{job_id}."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.job import Job
from app.schemas.job import JobStatusResponse

router = APIRouter()


def _calculate_progress(job: Job) -> Optional[float]:
    """Calculate progress based on job status and stored progress.

    v0.9.6: Returns actual progress from database if available.
    Returns None for jobs created before v0.9.6 (no progress data).

    Args:
        job: Job model instance

    Returns:
        Progress float (0.0-100.0) or None if not available
    """
    # v0.9.6: Return actual progress from database if available
    if job.progress is not None:
        return float(job.progress)

    # For jobs created before v0.9.6, return None to indicate no progress data
    # This distinguishes "no progress data" from "0% progress"
    return None


@router.get(
    "/v1/video/status/{job_id}", response_model=JobStatusResponse, deprecated=True
)
async def get_job_status(
    job_id: UUID, db: Session = Depends(get_db)
) -> JobStatusResponse:
    """Get status of a job.

    DEPRECATED: Use /v1/jobs/{job_id} instead. TODO: Remove in v1.0.0

    v0.9.6: Now returns actual progress from database when available.

    Args:
        job_id: UUID of the job
        db: Database session

    Returns:
        JobStatusResponse with status, progress, timestamps

    Raises:
        HTTPException: 404 if job not found
    """
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    progress = _calculate_progress(job)

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status.value,
        progress=progress,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
