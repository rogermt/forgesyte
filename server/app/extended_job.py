"""Extended Job Response Models for real-time features.

This module extends the base JobResponse model with optional fields
for real-time progress tracking and plugin timing information.

Author: Roger
Phase: 10 (Real-Time Infrastructure)
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models import JobResponse


class ExtendedJobResponse(JobResponse):
    """Extended job response with real-time fields.

    Adds optional fields for:
    - progress: Job progress percentage (0-100)
    - plugin_timings: Per-plugin execution timing data
    - warnings: Non-fatal warnings during execution
    """

    progress: Optional[int] = Field(
        default=None, ge=0, le=100, description="Job progress percentage (0-100)"
    )

    plugin_timings: Optional[Dict[str, float]] = Field(
        default=None,
        description="Per-plugin timing data in milliseconds (plugin_id -> timing_ms)",
    )

    warnings: Optional[List[str]] = Field(
        default_factory=list, description="Non-fatal warnings during job execution"
    )


class JobProgressUpdate(BaseModel):
    """Progress update message for real-time streaming."""

    job_id: str = Field(..., description="Job identifier")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    stage: Optional[str] = Field(default=None, description="Current processing stage")
    message: Optional[str] = Field(default=None, description="Status message")


class PluginTimingUpdate(BaseModel):
    """Plugin timing update message."""

    plugin_id: str = Field(..., description="Plugin identifier")
    timing_ms: float = Field(..., description="Execution time in milliseconds")
    clock_type: str = Field(default="monotonic", description="Clock type used")


class JobWarning(BaseModel):
    """Warning message for non-fatal issues."""

    plugin_id: Optional[str] = Field(
        default=None, description="Plugin that generated warning"
    )
    warning_code: Optional[str] = Field(default=None, description="Warning identifier")
    message: str = Field(..., description="Warning message")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional details"
    )
