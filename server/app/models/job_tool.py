"""JobTool SQLAlchemy ORM model for job_tools table.

v0.15.1: Replaces tool/tool_list columns with proper normalized table.
Each job can have multiple tools, stored as one row per tool.

NOTE: No ForeignKey constraint due to DuckDB bug #20246.
FK constraint causes false violations when UPDATE on jobs.progress
(jobs has index on progress, a non-PK column).
Integrity is enforced at application level via JobToolsService.
"""

import uuid

from duckdb_engine import UUID
from sqlalchemy import Column, Integer, String

from ..core.database import Base


class JobTool(Base):
    """JobTool database model for storing tools associated with a job.

    Replaces the denormalized tool/tool_list columns from the jobs table.
    This allows:
    - Unlimited tools per job
    - Proper indexing for efficient queries
    - Tool order preservation via tool_order column

    Note: No DB-level FK constraint due to DuckDB bug #20246.
    Use JobToolsService for all operations to ensure integrity.
    """

    __tablename__ = "job_tools"

    id = Column(
        UUID,
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # No ForeignKey - DuckDB bug #20246 triggers false FK violations
    # when UPDATE on jobs.progress (indexed non-PK column)
    # Integrity enforced by JobToolsService at application level
    job_id = Column(
        UUID,
        nullable=False,
    )

    tool_id = Column(
        String,
        nullable=False,
    )

    # Order of tool execution (0-indexed)
    tool_order = Column(
        Integer,
        nullable=False,
        default=0,
    )

    def __repr__(self) -> str:
        return f"<JobTool(id={self.id}, job_id={self.job_id}, tool_id={self.tool_id}, tool_order={self.tool_order})>"
