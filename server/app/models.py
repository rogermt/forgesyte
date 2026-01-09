"""Pydantic models for request/response validation."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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
    name: str
    description: str
    version: str = "1.0.0"
    inputs: List[str] = ["image"]
    outputs: List[str] = ["json"]
    permissions: List[str] = []
    config_schema: Optional[Dict[str, Any]] = None


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
