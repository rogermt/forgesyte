"""Health model for Phase 11 plugin health API.

Pydantic models for plugin health responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from ..lifecycle.lifecycle_state import PluginLifecycleState


class PluginHealthResponse(BaseModel):
    """Health status of a plugin. Queryable at /v1/plugins/{name}/health"""

    name: str = Field(..., description="Plugin name")
    state: PluginLifecycleState = Field(..., description="Current lifecycle state")
    description: Optional[str] = Field(
        None, description="Plugin description from manifest"
    )
    reason: Optional[str] = Field(
        None, description="Error reason if FAILED/UNAVAILABLE"
    )
    version: Optional[str] = Field(None, description="Plugin version from manifest")
    uptime_seconds: Optional[float] = Field(
        None, description="Seconds since loaded"
    )
    last_used: Optional[datetime] = Field(
        None, description="Last execution timestamp"
    )
    success_count: int = Field(0, description="Number of successful executions")
    error_count: int = Field(0, description="Number of failed executions")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "ocr",
                "state": "LOADED",
                "description": "Optical Character Recognition plugin",
                "version": "1.0.0",
                "success_count": 42,
                "error_count": 0,
                "uptime_seconds": 3600.5,
            }
        }


class PluginListResponse(BaseModel):
    """List of all plugins with health status"""

    plugins: list[PluginHealthResponse] = Field(..., description="List of plugins")
    total: int = Field(..., description="Total number of plugins")
    available: int = Field(
        ..., description="Number of available (LOADED/RUNNING) plugins"
    )
    failed: int = Field(..., description="Number of failed plugins")
    unavailable: int = Field(
        ..., description="Number of unavailable plugins"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "plugins": [
                    {
                        "name": "ocr",
                        "state": "LOADED",
                        "success_count": 42,
                    }
                ],
                "total": 2,
                "available": 1,
                "failed": 0,
                "unavailable": 1,
            }
        }
