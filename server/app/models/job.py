"""Job SQLAlchemy ORM model."""

import enum
import uuid
from datetime import datetime

from duckdb_engine import UUID
from sqlalchemy import Column, DateTime, Enum, Integer, String

from ..core.database import Base


class JobStatus(str, enum.Enum):
    """Job processing status enumeration."""

    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Job(Base):
    """Job database model for persistent job tracking.

    v0.15.1: tool/tool_list columns removed. Use job_tools table instead.
    See JobToolsService for application-level integrity.
    """

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

    # Plugin selection (tools are stored in job_tools table)
    plugin_id = Column(String, nullable=False)

    input_path = Column(String, nullable=False)
    output_path = Column(String, nullable=True)

    # Job type: "image", "image_multi", or "video" (v0.9.2 unified job system, v0.9.4 added image_multi)
    job_type = Column(String, nullable=False)

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

    # v0.9.6: Progress tracking for video jobs (0-100, null for pre-v0.9.6 jobs)
    progress = Column(
        Integer,
        nullable=True,
        default=None,
    )

    # v0.12.0: Ray future ID for job recovery after worker restart (Issue #270)
    ray_future_id = Column(
        String,
        nullable=True,
        default=None,
    )

    # v0.15.x: Pre-computed summary for /v1/jobs hot path (Discussion #354)
    # Summary is computed once during worker finalization and stored here
    # to avoid loading full artifacts on the list endpoint.
    summary = Column(
        String,
        nullable=True,
        default=None,
    )
