"""Job results endpoint: GET /video/results/{job_id}.

Clean Break (Issue #350): All jobs return result_url, not inline results.
"""

import json
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.job import Job, JobStatus
from app.schemas.job import JobResultsResponse
from app.services.storage.factory import get_storage_service
from app.settings import settings

router = APIRouter()
storage = get_storage_service(settings)


def _derive_video_summary(results: dict) -> dict:
    """Derive summary metadata from video job results.

    Issue #350: Extract lightweight metadata from large video results
    for display in job list without loading full results.
    """
    frame_count = 0
    detection_count = 0
    classes: List[str] = []

    # Handle frames array (most common structure)
    frames = results.get("frames", [])
    if frames:
        frame_count = len(frames)

        classes_set: set = set()
        for frame in frames:
            detections = frame.get("detections", [])
            detection_count += len(detections)
            for det in detections:
                if "class" in det:
                    classes_set.add(det["class"])

        classes = sorted(classes_set)

    # Handle tools structure (multi-tool video jobs)
    tools = results.get("tools", {})
    if tools:
        tool_detections = 0
        tool_classes: set = set()

        for _tool_name, tool_results in tools.items():
            if not isinstance(tool_results, dict):
                continue
            tool_frames = tool_results.get("frames", [])
            if not isinstance(tool_frames, list):
                continue
            for frame in tool_frames:
                detections = frame.get("detections", [])
                tool_detections += len(detections)
                for det in detections:
                    if "class" in det:
                        tool_classes.add(det["class"])

        # Add to existing counts
        detection_count += tool_detections
        classes = sorted(set(classes) | tool_classes)

    return {
        "frame_count": frame_count,
        "detection_count": detection_count,
        "classes": classes,
    }


@router.get(
    "/v1/video/results/{job_id}", response_model=JobResultsResponse, deprecated=True
)
async def get_job_results(
    job_id: UUID, db: Session = Depends(get_db)
) -> JobResultsResponse:
    """Get results of a completed job.

    DEPRECATED: Use /v1/jobs/{job_id} instead. TODO: Remove in v1.0.0

    Clean Break (Issue #350): Returns result_url and summary, not inline results.
    """
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.completed:
        raise HTTPException(status_code=404, detail="Job not completed")

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

    # Derive summary from results
    summary = _derive_video_summary(results)

    # Get signed URL for the result
    result_url = storage.get_signed_url(results_path)

    return JobResultsResponse(
        job_id=job.job_id,
        status=job.status.value if hasattr(job.status, "value") else str(job.status),
        plugin_id=job.plugin_id,
        result_url=result_url,
        summary=summary,
        job_type=job.job_type,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
