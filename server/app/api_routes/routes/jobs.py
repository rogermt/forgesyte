"""Unified jobs endpoint for v0.9.2.

Provides GET /v1/jobs/{job_id} endpoint that returns both status and results
for both image and video jobs, replacing the separate /v1/video/status and
/v1/video/results endpoints.

v0.9.3: Added GET /v1/jobs list endpoint for job listing with pagination.
v0.10.0: Added GET /v1/jobs/{job_id}/video endpoint for video file serving.
Issue #350: Added GET /v1/jobs/{job_id}/result endpoint for lazy loading.
"""

import json
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.job import Job, JobStatus
from app.schemas.job import JobListItem, JobListResponse, JobResultsResponse
from app.services.storage.factory import get_storage_service
from app.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()
storage = get_storage_service(settings)


def _extract_detections(frame: dict) -> List[dict]:
    """Extract detections list from frame, handling multiple formats.

    Handles:
    - detections: [...] (standard format)
    - detections: {"tracked_objects": [...]} (YOLO tracker format)

    Args:
        frame: Frame dict containing detections

    Returns:
        List of detection dicts, or empty list if not found/invalid
    """
    detections = frame.get("detections", [])
    if isinstance(detections, list):
        return detections
    if isinstance(detections, dict):
        # YOLO tracker format: {"tracked_objects": [...]}
        return detections.get("tracked_objects", [])
    return []


def _calculate_progress(status: JobStatus) -> int:
    """Calculate progress based on job status.

    Args:
        status: Job status enum

    Returns:
        Progress int (0-100): pending=0, running=50, completed/failed=100
        Issue #296: Changed from float to int to match DB model.
    """
    if status == JobStatus.pending:
        return 0
    elif status == JobStatus.running:
        return 50
    else:  # completed or failed
        return 100


def _derive_video_summary(results: dict) -> dict:
    """Derive summary metadata from video job results.

    Issue #350: Extract lightweight metadata from large video results
    for display in job list without loading full results.

    Discussion #353: Added defensive checks for malformed data.

    Args:
        results: Full video results dict

    Returns:
        Summary dict with frame_count, detection_count, classes
    """
    frame_count = 0
    detection_count = 0
    classes: List[str] = []

    # Known frame keys that are NOT tool payloads (from _merge_video_frames)
    KNOWN_FRAME_KEYS = {"frame_idx", "timestamp", "detections"}

    # Handle frames array (most common structure)
    frames = results.get("frames", [])
    if isinstance(frames, list):
        frame_count = len(frames)

        classes_set: set = set()
        for frame in frames:
            # Discussion #353: Defensive check - frame must be a dict
            if not isinstance(frame, dict):
                continue
            detections = _extract_detections(frame)
            detection_count += len(detections)
            for det in detections:
                # Discussion #353: Defensive check - det must be a dict
                if isinstance(det, dict) and "class" in det:
                    classes_set.add(det["class"])

            # Discussion #353: Handle video_multi merged frames structure
            # Each frame may have tool-specific keys (e.g., "player_tracker", "ball_detector")
            for key in frame:
                if key not in KNOWN_FRAME_KEYS:
                    # This is a tool payload
                    tool_payload = frame[key]
                    if isinstance(tool_payload, dict):
                        tool_dets = tool_payload.get("detections", [])
                        if isinstance(tool_dets, list):
                            detection_count += len(tool_dets)
                            for det in tool_dets:
                                if isinstance(det, dict) and "class" in det:
                                    classes_set.add(det["class"])

        classes = sorted(classes_set)

    # Handle tools structure (legacy multi-tool video jobs)
    tools = results.get("tools", {})
    if isinstance(tools, dict):
        tool_detections = 0
        tool_classes: set = set()

        for _tool_name, tool_results in tools.items():
            # Defensive: skip if tool_results is not a dict (malformed data)
            if not isinstance(tool_results, dict):
                continue
            tool_frames = tool_results.get("frames", [])
            # Defensive: skip if tool_frames is not a list
            if not isinstance(tool_frames, list):
                continue
            for frame in tool_frames:
                # Discussion #353: Defensive check - frame must be a dict
                if not isinstance(frame, dict):
                    continue
                detections = _extract_detections(frame)
                tool_detections += len(detections)
                for det in detections:
                    # Discussion #353: Defensive check - det must be a dict
                    if isinstance(det, dict) and "class" in det:
                        tool_classes.add(det["class"])

        # Add to existing counts
        detection_count += tool_detections
        classes = sorted(set(classes) | tool_classes)

    return {
        "frame_count": frame_count,
        "detection_count": detection_count,
        "classes": classes,
    }


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

    Issue #350: Video jobs return result_url and summary instead of inline result.

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

        result_url = None
        summary = None

        # Clean Break: All completed jobs return result_url + summary
        # No more inline results for any job type
        if job.status == JobStatus.completed and job.output_path:
            # Discussion #354: Use pre-computed summary from job.summary column
            # This avoids loading full artifacts on the hot path
            # Summary is separate from result_url - it's stored in DB
            if job.summary:
                try:
                    summary = json.loads(job.summary)
                except json.JSONDecodeError:
                    summary = None

            # Get signed URL for artifact download
            try:
                result_url = storage.get_signed_url(job.output_path)
            except FileNotFoundError:
                result_url = None

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
                result_url=result_url,  # Issue #350
                summary=summary,  # Issue #350
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

    Issue #350: Video jobs return result_url and summary instead of inline results.

    Discussion #356: Debug logging for diagnosing fetch issues.

    Args:
        job_id: UUID of the job
        db: Database session

    Returns:
        JobResultsResponse with job_id, status, results, error_message, timestamps

    Raises:
        HTTPException: 404 if job not found

    Note:
        - If job is not completed, results will be None
        - If job is completed, results will contain the output JSON (image jobs)
        - Video jobs return result_url and summary instead of results
        - Progress is calculated from job status
    """
    # Discussion #356: Debug logging for diagnosing fetch issues
    logger.debug("[JOB POLL] job_id=%s", job_id)

    from app.models.job_tool import JobTool

    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Query tools from job_tools table
    job_tools = (
        db.query(JobTool)
        .filter(JobTool.job_id == job_id)
        .order_by(JobTool.tool_order)
        .all()
    )
    tools = [jt.tool_id for jt in job_tools]

    # v0.9.7: Calculate multi-tool video metadata
    current_tool = None
    tools_total = None
    tools_completed = None

    if job.job_type in ("video", "video_multi") and len(tools) > 1:
        # Multi-tool video job: derive metadata
        tools_total = len(tools)

        if job.status == JobStatus.running and job.progress is not None:
            # Calculate which tool is running based on progress
            # Each tool gets equal weight (100/total_tools)
            tool_weight = 100 / tools_total
            # Issue #334: Use boundary comparison to avoid truncation bug
            # Boundaries mark where each tool completes: [33, 66] for 3 tools
            boundaries = [
                int((index + 1) * tool_weight) for index in range(tools_total - 1)
            ]
            tools_completed = sum(
                1 for boundary in boundaries if job.progress >= boundary
            )
            # Current tool is the next one after completed
            if tools_completed < tools_total:
                current_tool = tools[tools_completed]
        elif job.status == JobStatus.completed:
            tools_completed = tools_total
            current_tool = None  # All done

    # If job is not completed, return status without results
    if job.status != JobStatus.completed:
        return JobResultsResponse(
            job_id=job.job_id,
            status=job.status.value,  # Issue #211: Include status
            plugin_id=job.plugin_id,  # Issue #296: Was missing
            result_url=None,  # Issue #350
            summary=None,  # Issue #350
            tool=tools[0] if tools else None,
            tools=tools if len(tools) > 1 else None,
            job_type=job.job_type,
            error_message=job.error_message,
            progress=job.progress,  # Issue #296: Return int directly, DB stores Integer
            current_tool=current_tool,
            tools_total=tools_total,
            tools_completed=tools_completed,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    # Clean Break: All completed jobs return result_url + summary
    # No more inline results for any job type

    # Load results from storage to derive summary
    try:
        results_path = job.output_path
        file_path = storage.load_file(results_path)
        with open(file_path, "r") as f:
            results = json.load(f)
    except FileNotFoundError as err:
        raise HTTPException(status_code=404, detail="Results file not found") from err
    except json.JSONDecodeError as err:
        raise HTTPException(status_code=500, detail="Invalid results file") from err

    # Return result_url and summary for all completed jobs
    result_url = storage.get_signed_url(job.output_path)
    summary = _derive_video_summary(results)
    return JobResultsResponse(
        job_id=job.job_id,
        status=job.status.value,
        plugin_id=job.plugin_id,
        result_url=result_url,
        summary=summary,
        tool=tools[0] if tools else None,
        tools=tools if len(tools) > 1 else None,
        job_type=job.job_type,
        error_message=job.error_message,
        progress=job.progress,
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
        raise HTTPException(status_code=404, detail="Video file not found") from None

    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        filename=f"{job_id}.mp4",
    )
