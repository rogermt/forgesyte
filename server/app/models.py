"""Pydantic models for request/response validation.

This module defines data validation models using Pydantic v2. All models include
comprehensive Field descriptions for API documentation and validation constraints.

Models enforce data integrity at API boundaries, preventing invalid data from
entering the business logic layer.
"""

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
    """Request to analyze an image using a vision plugin.

    Attributes:
        plugin: Plugin identifier for analysis (e.g., "ocr_plugin", "motion_detector")
        options: Plugin-specific configuration options as key-value pairs
        image_url: HTTP(S) URL to fetch and analyze
    """

    plugin: str = Field(
        default="default",
        description="Plugin identifier (e.g., ocr_plugin, motion_detector)",
    )
    options: Optional[Dict[str, Any]] = Field(
        default=None, description="Plugin-specific analysis options"
    )
    image_url: Optional[str] = Field(
        default=None, description="HTTP(S) URL of image to fetch and analyze"
    )


class JobResponse(BaseModel):
    """Response containing analysis job status and results.

    Attributes:
        job_id: Unique job identifier for tracking
        status: Current job status (queued, running, done, error, not_found)
        result: Analysis results (only populated when status=done)
        error: Error message (only populated when status=error)
        created_at: ISO 8601 timestamp when job was created
        completed_at: ISO 8601 timestamp when job completed (null if in progress)
        plugin: Plugin used for analysis
        progress: Progress percentage (0-100) if available
    """

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    result: Optional[Dict[str, Any]] = Field(
        default=None, description="Analysis results (present when done)"
    )
    error: Optional[str] = Field(
        default=None, description="Error message (present when status=error)"
    )
    created_at: datetime = Field(..., description="Job creation timestamp")
    completed_at: Optional[datetime] = Field(
        default=None, description="Job completion timestamp"
    )
    plugin: str = Field(..., description="Plugin used for analysis")
    progress: Optional[float] = Field(
        default=None, description="Progress percentage (0-100)"
    )


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


class AnalysisResult(BaseModel):
    """Shared contract for plugin analysis results.

    All plugins must return this type from their analyze() method.
    Ensures consistent schema for results across all plugins and enables
    serialization to dict for storage and API responses.

    Attributes:
        text: Extracted or analyzed text content (e.g., OCR text).
              Can be empty string if no text extracted.
        blocks: List of detected regions/blocks with details.
                Structure depends on plugin (OCR blocks, motion regions, etc).
                Can be empty list if no regions detected.
        confidence: Overall confidence score (0.0-1.0).
                    Represents plugin's confidence in results.
        language: Detected language code (e.g., "eng", "fra").
                  Optional; only relevant for text-based plugins.
        error: Error message if analysis failed.
               Optional; only set when analysis encounters an error.
        extra: Plugin-specific results (e.g., YOLO detections, tracking data).
               Optional; structure depends on plugin.
    """

    text: str = Field(..., description="Extracted or analyzed text content")
    blocks: List[Dict[str, Any]] = Field(
        default_factory=list, description="Detected regions/blocks with details"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)"
    )
    language: Optional[str] = Field(
        default=None, description="Detected language code (e.g., 'eng', 'fra')"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if analysis failed"
    )
    extra: Optional[Dict[str, Any]] = Field(
        default=None, description="Plugin-specific results (e.g., YOLO detections)"
    )


class MCPTool(BaseModel):
    """MCP tool definition for plugin capabilities.

    Attributes:
        id: Unique tool identifier (matches plugin name)
        title: Human-readable tool title
        description: Tool description and capabilities
        inputs: List of input types accepted (e.g., "image", "config")
        outputs: List of output types produced (e.g., "json", "regions")
        invoke_endpoint: API endpoint to invoke this tool
        permissions: Required permissions to use this tool
    """

    id: str = Field(..., description="Unique tool identifier")
    title: str = Field(..., description="Human-readable tool title")
    description: str = Field(..., description="Tool description and capabilities")
    inputs: List[str] = Field(..., description="Accepted input types")
    outputs: List[str] = Field(..., description="Produced output types")
    invoke_endpoint: str = Field(..., description="API endpoint to invoke tool")
    permissions: List[str] = Field(
        default_factory=list, description="Required permissions to use"
    )


class MCPManifest(BaseModel):
    """MCP manifest describing available tools and server info.

    Attributes:
        tools: List of available MCP tools from plugins
        server: Server information (name, version, etc)
        version: MCP protocol version
    """

    tools: List[MCPTool] = Field(..., description="Available MCP tools")
    server: Dict[str, str] = Field(..., description="Server information")
    version: str = Field(default="1.0", description="MCP protocol version")


class WebSocketMessage(BaseModel):
    """WebSocket message protocol.

    Attributes:
        type: Message type (frame, result, error, status, ping, pong, etc)
        payload: Message-specific data structure
        timestamp: ISO 8601 timestamp when message was created
    """

    type: str = Field(
        ..., description="Message type (frame, result, error, status, ping, pong)"
    )
    payload: Dict[str, Any] = Field(..., description="Message-specific payload data")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message creation timestamp (ISO 8601)",
    )
