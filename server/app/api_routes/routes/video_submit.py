"""Video submission endpoint for Phase 16 job processing."""

from io import BytesIO
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, UploadFile

from app.core.database import SessionLocal
from app.models.job import Job, JobStatus
from app.services.storage.local_storage import LocalStorageService

router = APIRouter()
storage = LocalStorageService()


def validate_mp4_magic_bytes(data: bytes) -> None:
    """Validate that data contains MP4 magic bytes.

    Args:
        data: File bytes to validate

    Raises:
        HTTPException: If file is not a valid MP4
    """
    if b"ftyp" not in data[:64]:
        raise HTTPException(status_code=400, detail="Invalid MP4 file")


@router.post("/v1/video/submit")
async def submit_video(
    file: UploadFile,
    plugin_id: str = Query(..., description="Plugin ID from /v1/plugins"),
    tool: str = Query(..., description="Tool ID from plugin manifest"),
):
    """Submit a video file for processing.

    Args:
        file: MP4 video file to process
        plugin_id: ID of the plugin to use (from /v1/plugins)
        tool: ID of the tool to run (from plugin manifest)

    Returns:
        JSON with job_id for polling

    Raises:
        HTTPException: If file is invalid or processing fails
    """
    # Read and validate file
    contents = await file.read()
    validate_mp4_magic_bytes(contents)

    # Create job record
    job_id = str(uuid4())
    input_path = f"video/input/{job_id}.mp4"

    # Save file to storage
    storage.save_file(src=BytesIO(contents), dest_path=input_path)

    # Create database record
    db = SessionLocal()
    try:
        job = Job(
            job_id=job_id,
            status=JobStatus.pending,
            plugin_id=plugin_id,
            tool=tool,
            input_path=input_path,
            job_type="video",
        )
        db.add(job)
        db.commit()
    finally:
        db.close()

    return {"job_id": job_id}
