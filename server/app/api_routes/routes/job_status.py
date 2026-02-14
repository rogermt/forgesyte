"""Job status endpoint: GET /video/status/{job_id}."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.job import Job, JobStatus
from app.schemas.job import JobStatusResponse

router = APIRouter()


def _calculate_progress(status: JobStatus) -> float:
    """Calculate progress based on job status.

    Args:
        status: Job status enum

    Returns:
        Progress float: pending=0.0, running=0.5, completed/failed=1.0
    """
    if status == JobStatus.pending:
        return 0.0
    elif status == JobStatus.running:
        return 0.5
    else:  # completed or failed
        return 1.0


@router.get("/v1/video/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: UUID, db: Session = Depends(get_db)) -> JobStatusResponse:
    """Get status of a job.

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

    progress = _calculate_progress(job.status)

    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status.value,
        progress=progress,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
