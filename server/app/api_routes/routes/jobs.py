"""Unified jobs endpoint for v0.9.2.

Provides GET /v1/jobs/{job_id} endpoint that returns both status and results
for both image and video jobs, replacing the separate /v1/video/status and
/v1/video/results endpoints.
"""

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.job import Job, JobStatus
from app.schemas.job import JobResultsResponse
from app.services.storage.local_storage import LocalStorageService

router = APIRouter()
storage = LocalStorageService()


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


@router.get("/v1/jobs/{job_id}", response_model=JobResultsResponse)
async def get_job(job_id: UUID, db: Session = Depends(get_db)) -> JobResultsResponse:
    """Get job status and results (unified for image and video).

    This endpoint replaces /v1/video/status/{job_id} and
    /v1/video/results/{job_id}. It returns both status and results
    in a single response for both image and video jobs.

    Args:
        job_id: UUID of the job
        db: Database session

    Returns:
        JobResultsResponse with job_id, status, results, error_message, timestamps

    Raises:
        HTTPException: 404 if job not found

    Note:
        - If job is not completed, results will be None
        - If job is completed, results will contain the output JSON
        - Progress is calculated from job status
    """
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # If job is not completed, return status without results
    if job.status != JobStatus.completed:
        return JobResultsResponse(
            job_id=job.job_id,
            status=job.status.value,  # Issue #211: Include status
            results=None,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    # Load results from storage
    try:
        results_path = job.output_path
        file_path = storage.load_file(results_path)
        with open(file_path, "r") as f:
            results = json.load(f)
    except FileNotFoundError as err:
        raise HTTPException(status_code=404, detail="Results file not found") from err
    except json.JSONDecodeError as err:
        raise HTTPException(status_code=500, detail="Invalid results file") from err

    return JobResultsResponse(
        job_id=job.job_id,
        status=job.status.value,  # Issue #211: Include status
        results=results,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
