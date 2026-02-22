"""Schemas for job endpoints."""

from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class JobStatusResponse(BaseModel):
    """Response for GET /video/status/{job_id}."""

    job_id: UUID
    status: Literal["pending", "running", "completed", "failed"]
    progress: float
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class JobResultsResponse(BaseModel):
    """Response for GET /v1/jobs/{job_id} (unified endpoint).

    Issue #211: Added status field for web-UI polling.
    v0.9.4: Added tool_list and job_type for multi-tool support.
    """

    job_id: UUID
    status: str  # "pending", "running", "completed", "failed"
    results: dict | None
    tool: Optional[str] = None  # v0.9.4: Single tool (backward compatible)
    tool_list: Optional[List[str]] = None  # v0.9.4: Multi-tool list
    job_type: Optional[str] = None  # v0.9.4: "image" | "image_multi" | "video"
    error_message: Optional[str] = None
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
