"""JobToolsService - Application-level integrity for job_tools relationships.

Provides a wrapper for managing job_tools table operations with proper
validation and cleanup. Replaces DB-level FK constraint due to DuckDB bug #20246.

Bug #20246: UPDATE on indexed non-PK column triggers false FK violation.
Solution: Remove DB FK constraint, enforce integrity at application level.

Usage:
    from app.services.job_tools_service import JobToolsService

    # Add tools to a job
    JobToolsService.add_tools_to_job(db, job_id, ["tool1", "tool2"])

    # Get tools for a job
    tools = JobToolsService.get_tools_for_job(db, job_id)

    # Delete tools when job is deleted
    JobToolsService.delete_tools_for_job(db, job_id)
"""

import logging
import uuid
from typing import List

from sqlalchemy.orm import Session

from ..models.job import Job
from ..models.job_tool import JobTool

logger = logging.getLogger(__name__)


class JobToolsService:
    """Service for managing job_tools relationships with application-level integrity.

    This service centralizes all job_tools operations and ensures:
    1. Job exists before adding tools (validate_job_exists)
    2. Tools are properly ordered (tool_order)
    3. Tools are cleaned up when job is deleted (delete_tools_for_job)

    Since DuckDB doesn't support reliable FK constraints with indexed columns,
    this service provides the integrity that would normally be at DB level.
    """

    @staticmethod
    def add_tools_to_job(db: Session, job_id: uuid.UUID, tools: List[str]) -> None:
        """Add tools to a job with validation.

        Args:
            db: Database session
            job_id: UUID of the job
            tools: List of tool IDs to add (order preserved)

        Raises:
            ValueError: If job does not exist

        Example:
            >>> JobToolsService.add_tools_to_job(db, job_id, ["ocr", "yolo"])
        """
        # Validate job exists
        if not JobToolsService.validate_job_exists(db, job_id):
            raise ValueError(f"Job {job_id} does not exist, cannot add tools")

        # Add each tool with its order
        for order, tool_id in enumerate(tools):
            job_tool = JobTool(
                id=uuid.uuid4(),
                job_id=job_id,
                tool_id=tool_id,
                tool_order=order,
            )
            db.add(job_tool)

        logger.debug(f"Added {len(tools)} tools to job {job_id}: {tools}")

    @staticmethod
    def get_tools_for_job(db: Session, job_id: uuid.UUID) -> List[str]:
        """Get ordered list of tools for a job.

        Args:
            db: Database session
            job_id: UUID of the job

        Returns:
            List of tool IDs in execution order

        Example:
            >>> tools = JobToolsService.get_tools_for_job(db, job_id)
            >>> print(tools)
            ["ocr", "yolo"]
        """
        job_tools = (
            db.query(JobTool)
            .filter(JobTool.job_id == job_id)
            .order_by(JobTool.tool_order)
            .all()
        )

        tools = [jt.tool_id for jt in job_tools]
        logger.debug(f"Retrieved {len(tools)} tools for job {job_id}: {tools}")
        return tools

    @staticmethod
    def delete_tools_for_job(db: Session, job_id: uuid.UUID) -> int:
        """Delete all tools for a job (CASCADE replacement).

        Call this when deleting a job to clean up associated tools.
        Replaces ON DELETE CASCADE which DuckDB doesn't support.

        Args:
            db: Database session
            job_id: UUID of the job being deleted

        Returns:
            Number of tool records deleted

        Example:
            >>> deleted_count = JobToolsService.delete_tools_for_job(db, job_id)
            >>> print(f"Deleted {deleted_count} tools")
        """
        count = db.query(JobTool).filter(JobTool.job_id == job_id).delete()
        logger.debug(f"Deleted {count} tools for job {job_id}")
        return count

    @staticmethod
    def validate_job_exists(db: Session, job_id: uuid.UUID) -> bool:
        """Check if a job exists in the database.

        Args:
            db: Database session
            job_id: UUID of the job to check

        Returns:
            True if job exists, False otherwise

        Example:
            >>> if JobToolsService.validate_job_exists(db, job_id):
            ...     JobToolsService.add_tools_to_job(db, job_id, tools)
        """
        job = db.query(Job).filter(Job.job_id == job_id).first()
        exists = job is not None
        logger.debug(f"Job {job_id} exists: {exists}")
        return exists

    @staticmethod
    def replace_tools_for_job(db: Session, job_id: uuid.UUID, tools: List[str]) -> None:
        """Replace all tools for a job (delete + add).

        Useful for updating tool list without creating duplicates.

        Args:
            db: Database session
            job_id: UUID of the job
            tools: New list of tool IDs

        Raises:
            ValueError: If job does not exist

        Example:
            >>> JobToolsService.replace_tools_for_job(db, job_id, ["new_tool"])
        """
        JobToolsService.delete_tools_for_job(db, job_id)
        JobToolsService.add_tools_to_job(db, job_id, tools)
        logger.debug(f"Replaced tools for job {job_id} with: {tools}")
