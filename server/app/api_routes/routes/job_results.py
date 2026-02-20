"""Job results endpoint: GET /video/results/{job_id}."""

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


@router.get("/v1/video/results/{job_id}", response_model=JobResultsResponse)
async def get_job_results(
    job_id: UUID, db: Session = Depends(get_db)
) -> JobResultsResponse:
    """Get results of a completed job.

    Args:
        job_id: UUID of the job
        db: Database session

    Returns:
        JobResultsResponse with results, timestamps

    Raises:
        HTTPException: 404 if job not found or not completed
    """
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.completed:
        raise HTTPException(status_code=404, detail="Job not completed")

    # Load results from storage
    # job.output_path is already a full path (from LocalStorageService.save_file)
    try:
        results_path = job.output_path
        with open(results_path, "r") as f:
            results = json.load(f)
    except FileNotFoundError as err:
        raise HTTPException(status_code=404, detail="Results file not found") from err
    except json.JSONDecodeError as err:
        raise HTTPException(status_code=500, detail="Invalid results file") from err

    return JobResultsResponse(
        job_id=job.job_id,
        results=results,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
