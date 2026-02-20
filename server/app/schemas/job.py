"""Schemas for job endpoints."""

from datetime import datetime
from typing import Literal
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
    """Response for GET /v1/jobs/{job_id} (unified endpoint)."""

    job_id: UUID
    results: dict | None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True
