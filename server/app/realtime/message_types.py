"""
Phase 10 Real-Time Message Types

Defines the typed message schema for WebSocket real-time communication.

Message Format:
{
    "type": "<message-type>",
    "payload": { },
    "timestamp": "<ISO8601>"
}

TODO: Implement the following message types:
- frame: Annotated frame from plugin
- partial_result: Intermediate plugin result
- progress: Job progress update (0-100)
- plugin_status: Plugin execution status
- warning: Non-fatal plugin warning
- error: Fatal error message
- ping: Heartbeat from server
- pong: Heartbeat response from client
- metadata: Plugin metadata on connection

Author: Roger
Phase: 10
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Enumeration of all valid real-time message types."""

    FRAME = "frame"
    PARTIAL_RESULT = "partial_result"
    PROGRESS = "progress"
    PLUGIN_STATUS = "plugin_status"
    WARNING = "warning"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"
    METADATA = "metadata"


class RealtimeMessage(BaseModel):
    """
    Schema for all real-time WebSocket messages.

    Attributes:
        type: The message type (frame, partial_result, progress, etc.)
        payload: Message-specific data
        timestamp: ISO8601 timestamp of message creation
    """

    type: MessageType
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class ProgressPayload(BaseModel):
    """Payload for progress update messages."""

    job_id: str
    progress: int = Field(ge=0, le=100, description="Progress percentage (0-100)")
    stage: Optional[str] = None
    message: Optional[str] = None


class PluginStatusPayload(BaseModel):
    """Payload for plugin status messages."""

    plugin_id: str
    status: Literal["started", "running", "completed", "failed"]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class PluginTimingPayload(BaseModel):
    """Payload for plugin timing messages."""

    plugin_id: str
    timing_ms: float = Field(ge=0, description="Execution time in milliseconds")
    clock_type: Literal["monotonic"] = "monotonic"


class WarningPayload(BaseModel):
    """Payload for warning messages."""

    plugin_id: Optional[str] = None
    warning_code: Optional[str] = None
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorPayload(BaseModel):
    """Payload for error messages."""

    plugin_id: Optional[str] = None
    error_code: Optional[str] = None
    message: str
    details: Optional[Dict[str, Any]] = None
    fatal: bool = False


class MetadataPayload(BaseModel):
    """Payload for metadata messages sent on connection."""

    plugins: list[Dict[str, Any]] = Field(default_factory=list)
    server_version: str
    capabilities: list[str] = Field(default_factory=list)


# TODO: Implement frame payload
# class FramePayload(BaseModel):
#     """Payload for frame messages."""
#     frame_id: str
#     plugin_id: str
#     data: bytes  # or base64 encoded
#     annotations: list[Dict[str, Any]] = Field(default_factory=list)


# TODO: Implement partial_result payload
# class PartialResultPayload(BaseModel):
#     """Payload for partial result messages."""
#     job_id: str
#     plugin_id: str
#     result: Dict[str, Any]
#     confidence: Optional[float] = None
