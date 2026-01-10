"""Pydantic models for request/response validation."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
    NOT_FOUND = "not_found"


class AnalyzeRequest(BaseModel):
    plugin: str = Field(default="default", description="Plugin to use for analysis")
    options: Optional[Dict[str, Any]] = Field(
        default=None, description="Plugin-specific options"
    )
    image_url: Optional[str] = Field(
        default=None, description="URL of image to analyze"
    )


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    plugin: str
    progress: Optional[float] = None


class PluginMetadata(BaseModel):
    """Plugin metadata schema with strict validation.

    Attributes:
        name: Plugin identifier (required, non-empty string).
              Use lowercase with underscores or hyphens.
              Examples: "ocr_plugin", "motion-detector"
        description: Human-readable plugin description (required, non-empty)
        version: Semantic version string (default: "1.0.0")
                 Supports: "1.0.0", "2.1", "1.0.0-alpha", "1.0.0+build.123"
        inputs: List of input types the plugin accepts (default: ["image"])
                Examples: ["image"], ["image", "config"], []
        outputs: List of output types the plugin produces (default: ["json"])
                 Examples: ["json"], ["text", "confidence"], ["regions"]
        permissions: List of permissions required (default: [])
                     Format: "resource:action"
                     Examples: "read:files", "write:results", "gpu:access"
        config_schema: Optional JSON Schema defining configuration options.
                       Structure: dict with parameter names as keys containing
                       type, default, description, etc.
    """

    name: str = Field(
        ...,
        min_length=1,
        description="Plugin identifier (non-empty, required)",
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Human-readable plugin description (non-empty, required)",
    )
    version: str = Field(
        default="1.0.0",
        description="Semantic version string (default: 1.0.0)",
    )
    inputs: List[str] = Field(
        default_factory=lambda: ["image"],
        description="Input types accepted by plugin",
    )
    outputs: List[str] = Field(
        default_factory=lambda: ["json"],
        description="Output types produced by plugin",
    )
    permissions: List[str] = Field(
        default_factory=list,
        description="Required permissions (format: resource:action)",
    )
    config_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON Schema for plugin configuration options",
    )

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: Any) -> str:
        """Validate plugin name is non-empty string."""
        if isinstance(v, str) and v.strip():
            return v
        raise ValueError("name must be a non-empty string")

    @field_validator("description", mode="before")
    @classmethod
    def validate_description(cls, v: Any) -> str:
        """Validate description is non-empty string."""
        if isinstance(v, str) and v.strip():
            return v
        raise ValueError("description must be a non-empty string")


class MCPTool(BaseModel):
    id: str
    title: str
    description: str
    inputs: List[str]
    outputs: List[str]
    invoke_endpoint: str
    permissions: List[str] = []


class MCPManifest(BaseModel):
    tools: List[MCPTool]
    server: Dict[str, str]
    version: str = "1.0"


class WebSocketMessage(BaseModel):
    type: str  # "frame", "result", "error", "status"
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
