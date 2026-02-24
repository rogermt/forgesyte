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

    # Plugin and tool selection (replaces pipeline_id + tools)
    plugin_id = Column(String, nullable=False)
    tool = Column(String, nullable=True)  # v0.9.4: Nullable for multi-tool jobs
    tool_list = Column(
        String, nullable=True
    )  # v0.9.4: JSON-encoded list for multi-tool jobs

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
