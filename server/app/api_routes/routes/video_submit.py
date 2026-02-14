"""Video submission endpoint for Phase 16 job processing."""

from io import BytesIO
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.core.database import SessionLocal
from app.models.job import Job, JobStatus
from app.services.queue.memory_queue import InMemoryQueueService
from app.services.storage.local_storage import LocalStorageService

router = APIRouter()
storage = LocalStorageService()
queue = InMemoryQueueService()


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
    pipeline_id: str,
):
    """Submit a video file for processing.

    Args:
        file: MP4 video file to process
        pipeline_id: ID of the pipeline to use (e.g., "yolo_ocr")

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
    input_path = f"{job_id}.mp4"

    # Save file to storage
    storage.save_file(src=BytesIO(contents), dest_path=input_path)

    # Create database record
    db = SessionLocal()
    try:
        job = Job(
            job_id=job_id,
            status=JobStatus.pending,
            pipeline_id=pipeline_id,
            input_path=input_path,
        )
        db.add(job)
        db.commit()
    finally:
        db.close()

    # Enqueue for processing
    queue.enqueue(job_id)

    return {"job_id": job_id}
