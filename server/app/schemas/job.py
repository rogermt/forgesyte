"""Schemas for job endpoints."""

from datetime import datetime
from typing import Literal, Optional
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
    """

    job_id: UUID
    status: str  # "pending", "running", "completed", "failed"
    results: dict | None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True
