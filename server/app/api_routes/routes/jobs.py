"""Unified jobs endpoint for v0.9.2.

Provides GET /v1/jobs/{job_id} endpoint that returns both status and results
for both image and video jobs, replacing the separate /v1/video/status and
/v1/video/results endpoints.

v0.9.3: Added GET /v1/jobs list endpoint for job listing with pagination.
v0.10.0: Added GET /v1/jobs/{job_id}/video endpoint for video file serving.
"""

import json
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.job import Job, JobStatus
from app.schemas.job import JobListItem, JobListResponse, JobResultsResponse
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


@router.get("/v1/jobs", response_model=JobListResponse)
async def list_jobs(
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of jobs to return"
    ),
    skip: int = Query(0, ge=0, description="Number of jobs to skip for pagination"),
    db: Session = Depends(get_db),
) -> JobListResponse:
    """List jobs with pagination.

    Returns a paginated list of jobs ordered by creation date (newest first).
    Results are only loaded for completed jobs.

    Args:
        limit: Maximum number of jobs to return (1-100, default 10)
        skip: Number of jobs to skip for pagination (default 0)
        db: Database session

    Returns:
        JobListResponse with jobs array and total count
    """
    # Query jobs with pagination
    query = db.query(Job).order_by(Job.created_at.desc())
    total_count = query.count()
    jobs = query.offset(skip).limit(limit).all()

    # Transform jobs to response format
    job_items: List[JobListItem] = []

    for job in jobs:
        # Calculate progress
        progress = _calculate_progress(job.status)

        # Load results only for completed jobs
        result = None
        if job.status == JobStatus.completed and job.output_path:
            try:
                file_path = storage.load_file(job.output_path)
                with open(file_path, "r") as f:
                    result = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                result = None

        # Build job item
        job_items.append(
            JobListItem(
                job_id=str(job.job_id),
                status=job.status.value,  # Issue #212: Use aligned status values
                plugin=job.plugin_id,
                created_at=job.created_at,
                completed_at=(
                    job.updated_at
                    if job.status in (JobStatus.completed, JobStatus.failed)
                    else None
                ),
                result=result,
                error=job.error_message,
                progress=progress,
            )
        )

    return JobListResponse(jobs=job_items, count=total_count)


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

    # Parse tool_list from JSON if present
    tool_list = json.loads(job.tool_list) if job.tool_list else None

    # v0.9.7: Calculate multi-tool video metadata
    current_tool = None
    tools_total = None
    tools_completed = None

    if job.job_type == "video" and job.tool_list:
        # Multi-tool video job: derive metadata
        try:
            tools_list = json.loads(job.tool_list)
            tools_total = len(tools_list)

            if job.status == JobStatus.running and job.progress is not None:
                # Calculate which tool is running based on progress
                # Each tool gets equal weight (100/total_tools)
                tool_weight = 100 / tools_total
                tools_completed = int(job.progress / tool_weight)
                # Clamp to valid range
                tools_completed = max(0, min(tools_total - 1, tools_completed))
                # Current tool is the next one after completed
                if tools_completed < tools_total:
                    current_tool = tools_list[tools_completed]
            elif job.status == JobStatus.completed:
                tools_completed = tools_total
                current_tool = None  # All done
        except (json.JSONDecodeError, ZeroDivisionError):
            pass

    # If job is not completed, return status without results
    if job.status != JobStatus.completed:
        return JobResultsResponse(
            job_id=job.job_id,
            status=job.status.value,  # Issue #211: Include status
            results=None,
            tool=job.tool,
            tool_list=tool_list,
            job_type=job.job_type,
            error_message=job.error_message,
            progress=float(job.progress) if job.progress is not None else None,
            current_tool=current_tool,
            tools_total=tools_total,
            tools_completed=tools_completed,
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
        tool=job.tool,
        tool_list=tool_list,
        job_type=job.job_type,
        error_message=job.error_message,
        progress=float(job.progress) if job.progress is not None else None,
        current_tool=current_tool,
        tools_total=tools_total,
        tools_completed=tools_completed,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("/v1/jobs/{job_id}/video")
async def get_job_video(job_id: UUID, db: Session = Depends(get_db)) -> FileResponse:
    """Get the uploaded video file for playback in VideoResultsViewer.

    Serves the original uploaded video file stored at video/input/{job_id}.mp4.
    This is used by the frontend VideoResultsViewer component for video playback
    with overlay rendering.

    Args:
        job_id: UUID of the job
        db: Database session

    Returns:
        FileResponse with video/mp4 content type

    Raises:
        HTTPException: 404 if job not found or video file not found
    """
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get the input video path from job record
    if not job.input_path:
        raise HTTPException(status_code=404, detail="Video file not found")

    try:
        video_path = storage.load_file(job.input_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        filename=f"{job_id}.mp4",
    )
