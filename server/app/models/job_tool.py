"""JobTool SQLAlchemy ORM model for job_tools table.

v0.15.1: Replaces tool/tool_list columns with proper normalized table.
Each job can have multiple tools, stored as one row per tool.
"""

import uuid

from duckdb_engine import UUID
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..core.database import Base


class JobTool(Base):
    """JobTool database model for storing tools associated with a job.

    Replaces the denormalized tool/tool_list columns from the jobs table.
    This allows:
    - Unlimited tools per job
    - Proper indexing and foreign keys
    - Efficient queries and analytics
    - Tool order preservation via tool_order column
    """

    __tablename__ = "job_tools"

    id = Column(
        UUID,
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    job_id = Column(
        UUID,
        ForeignKey("jobs.job_id"),
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

    # Relationship back to Job (optional, for convenience)
    job = relationship("Job", backref="job_tools")

    def __repr__(self) -> str:
        return f"<JobTool(id={self.id}, job_id={self.job_id}, tool_id={self.tool_id}, tool_order={self.tool_order})>"
