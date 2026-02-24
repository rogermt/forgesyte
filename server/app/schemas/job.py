"""Schemas for job endpoints."""

from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class JobStatusResponse(BaseModel):
    """Response for GET /video/status/{job_id}.

    v0.9.6: progress is Optional[float] - null for pre-v0.9.6 jobs.
    """

    job_id: UUID
    status: Literal["pending", "running", "completed", "failed"]
    progress: Optional[float]  # v0.9.6: None for pre-v0.9.6 jobs
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class JobResultsResponse(BaseModel):
    """Response for GET /v1/jobs/{job_id} (unified endpoint).

    Issue #211: Added status field for web-UI polling.
    v0.9.4: Added tool_list and job_type for multi-tool support.
    v0.9.6: Added progress field for video job progress tracking.
    v0.9.7: Added current_tool, tools_total, tools_completed for multi-tool video jobs.
    """

    job_id: UUID
    status: str  # "pending", "running", "completed", "failed"
    results: dict | None
    tool: Optional[str] = None  # v0.9.4: Single tool (backward compatible)
    tool_list: Optional[List[str]] = None  # v0.9.4: Multi-tool list
    job_type: Optional[str] = None  # v0.9.4: "image" | "image_multi" | "video"
    error_message: Optional[str] = None
    progress: Optional[float] = None  # v0.9.6: None for pre-v0.9.6 jobs
    # v0.9.7: Multi-tool video job metadata (derived, not stored)
    current_tool: Optional[str] = None  # Current tool being processed
    tools_total: Optional[int] = None  # Total number of tools
    tools_completed: Optional[int] = None  # Number of tools completed
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class JobListItem(BaseModel):
    """Single job item in list response for GET /v1/jobs."""

    job_id: str
    status: str  # "pending", "running", "completed", "failed" (Issue #212 aligned)
    plugin: str  # plugin_id
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    progress: Optional[float] = None


class JobListResponse(BaseModel):
    """Response for GET /v1/jobs list endpoint."""

    jobs: List[JobListItem]
    count: int
