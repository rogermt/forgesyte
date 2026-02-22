# Current Source Snapshot — Worker Pipeline Files

**Date**: 2026-02-19  
**Purpose**: Pre-patch snapshot of the 4 files involved in worker job pickup

---

## 1. `server/app/api_routes/routes/video_submit.py`

```python
"""Video submission endpoint for Phase 16 job processing."""

from io import BytesIO
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, UploadFile

from app.core.database import SessionLocal
from app.models.job import Job, JobStatus
from app.services.queue.memory_queue import InMemoryQueueService
from app.services.storage.local_storage import LocalStorageService

router = APIRouter()
storage = LocalStorageService()
queue = InMemoryQueueService()

DEFAULT_VIDEO_PIPELINE = "ocr_only"


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
    pipeline_id: str = Query(
        default=DEFAULT_VIDEO_PIPELINE,
        description="Pipeline ID (optional, defaults to ocr_only)",
    ),
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
```

---

## 2. `server/app/workers/worker.py`

```python
"""Job worker for Phase 16 asynchronous processing.

This worker:
1. Dequeues job_ids from the queue
2. Updates job status to RUNNING
3. Executes pipeline on input file (Commit 6)
4. Saves results to storage as JSON
5. Handles errors with graceful failure
6. Handles signals (SIGINT/SIGTERM) for graceful shutdown
"""

import json
import logging
import signal
import time
from io import BytesIO
from typing import Optional, Protocol

from .worker_state import worker_last_heartbeat
from ..core.database import SessionLocal
from ..models.job import Job, JobStatus
from ..services.queue.memory_queue import InMemoryQueueService

logger = logging.getLogger(__name__)


class StorageService(Protocol):
    """Protocol for storage service (allows dependency injection)."""

    def load_file(self, path: str):
        """Load file from storage."""
        ...

    def save_file(self, src, dest_path: str) -> str:
        """Save file to storage."""
        ...


class PipelineService(Protocol):
    """Protocol for pipeline service (allows dependency injection)."""

    def run_on_file(
        self,
        mp4_path: str,
        pipeline_id: str,
        frame_stride: int = 1,
        max_frames: Optional[int] = None,
    ):
        """Execute pipeline on video file."""
        ...


class JobWorker:
    """Processes jobs from the queue."""

    def __init__(
        self,
        queue: Optional[InMemoryQueueService] = None,
        session_factory=None,
        storage: Optional[StorageService] = None,
        pipeline_service: Optional[PipelineService] = None,
    ) -> None:
        """Initialize worker with queue service.

        Args:
            queue: QueueService instance (defaults to InMemoryQueueService)
            session_factory: Session factory (defaults to SessionLocal from database.py)
            storage: StorageService instance for file I/O
            pipeline_service: PipelineService instance for pipeline execution
        """
        self._queue = queue or InMemoryQueueService()
        self._session_factory = session_factory or SessionLocal
        self._storage = storage
        self._pipeline_service = pipeline_service
        self._running = True

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum: int, frame) -> None:
        """Handle shutdown signals gracefully.

        Args:
            signum: Signal number (SIGINT, SIGTERM)
            frame: Signal frame
        """
        logger.info("Received signal %s, shutting down gracefully", signum)
        self._running = False

    def run_once(self) -> bool:
        """Process one job from the queue.

        Returns:
            True if a job was processed, False if queue was empty
        """
        job_id = self._queue.dequeue()
        if job_id is None:
            return False

        db = self._session_factory()
        try:
            job = db.query(Job).filter(Job.job_id == job_id).first()

            if job is None:
                logger.warning("Dequeued job %s but no DB record found", job_id)
                return False

            job.status = JobStatus.running
            db.commit()

            logger.info("Job %s marked RUNNING", job_id)

            # COMMIT 6: Execute pipeline on input file
            return self._execute_pipeline(job, db)
        finally:
            db.close()

    def _execute_pipeline(self, job: Job, db) -> bool:
        """Execute pipeline on job input file.

        Args:
            job: Job model instance
            db: Database session

        Returns:
            True if pipeline executed successfully, False on error
        """
        try:
            # Verify storage and pipeline services are available
            if not self._storage or not self._pipeline_service:
                logger.warning(
                    "Job %s: storage or pipeline service not available", job.job_id
                )
                job.status = JobStatus.failed
                job.error_message = "Pipeline execution services not configured"
                db.commit()
                return False

            # Load input file from storage
            input_file_path = self._storage.load_file(job.input_path)
            logger.info("Job %s: loaded input file %s", job.job_id, input_file_path)

            # Execute pipeline on video file
            results = self._pipeline_service.run_on_file(
                str(input_file_path),
                job.pipeline_id,
            )
            logger.info(
                "Job %s: pipeline executed, %d results", job.job_id, len(results)
            )

            # Prepare JSON output
            output_data = {"results": results}
            output_json = json.dumps(output_data)
            output_bytes = BytesIO(output_json.encode())

            # Save results to storage
            output_path = self._storage.save_file(
                output_bytes,
                f"output/{job.job_id}.json",
            )
            logger.info("Job %s: saved results to %s", job.job_id, output_path)

            # Mark job as completed
            job.status = JobStatus.completed
            job.output_path = output_path
            job.error_message = None
            db.commit()

            logger.info("Job %s marked COMPLETED", job.job_id)
            return True

        except Exception as e:
            # Mark job as failed with error message
            logger.error("Job %s: pipeline execution failed: %s", job.job_id, str(e))
            job.status = JobStatus.failed
            job.error_message = str(e)
            db.commit()
            return False

    def run_forever(self) -> None:
        """Run the worker loop until shutdown signal is received."""
        logger.info("Worker started")
        while self._running:
            # Send heartbeat to indicate worker is alive
            worker_last_heartbeat.beat()

            processed = self.run_once()
            if not processed:
                time.sleep(0.5)
        logger.info("Worker stopped")
```

---

## 3. `server/app/models/job.py`

```python
"""Job SQLAlchemy ORM model."""

import enum
import uuid
from datetime import datetime

from duckdb_engine import UUID
from sqlalchemy import Column, DateTime, Enum, String

from ..core.database import Base


class JobStatus(str, enum.Enum):
    """Job processing status enumeration."""

    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Job(Base):
    """Job database model for persistent job tracking."""

    __tablename__ = "jobs"

    job_id = Column(
        UUID,
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    status = Column(
        Enum(JobStatus, name="job_status_enum"),
        nullable=False,
        default=JobStatus.pending,
    )

    pipeline_id = Column(String, nullable=False)

    input_path = Column(String, nullable=False)
    output_path = Column(String, nullable=True)

    error_message = Column(String, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
```

---

## 4. `server/app/core/database.py`

```python
"""DuckDB SQLAlchemy database configuration."""

from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base: Any = declarative_base()

# Ensure data directory exists
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# File-based DuckDB for application runtime
engine = create_engine(
    "duckdb:///data/foregsyte.duckdb",
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def init_db():
    """Initialize database schema - create tables if they don't exist."""
    try:
        # Import models to register them with Base
        from ..models.job import Job  # noqa: F401

        # Create all tables defined in models
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        raise RuntimeError(f"Could not initialize database schema: {e}") from e


def get_db():
    """Dependency for FastAPI to inject database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
