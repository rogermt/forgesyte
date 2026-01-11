"""JSON-RPC 2.0 protocol implementation for MCP transport."""

from enum import IntEnum
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field, field_validator


class JSONRPCErrorCode(IntEnum):
    """JSON-RPC 2.0 standard error codes."""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603


class JSONRPCError(BaseModel):
    """JSON-RPC 2.0 error object.

    Represents a JSON-RPC error response containing error code, message,
    and optional additional data about the error.

    Attributes:
        code: Integer error code (standard or custom).
              Standard codes: -32700 to -32603
              Server errors: -32000 to -32099
        message: Human-readable error description.
        data: Optional additional information about the error.
    """

    code: int = Field(..., description="Error code (required)")
    message: str = Field(..., description="Error message (required)")
    data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error context data (optional)",
    )


class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 request object.

    Represents a JSON-RPC 2.0 request with method call parameters.
    Can be a request (with id) or notification (without id).

    Attributes:
        jsonrpc: JSON-RPC protocol version (must be "2.0").
        method: Name of the method to invoke (e.g., "tools/list", "initialize").
        params: Parameters for the method (dict). Defaults to empty dict.
        id: Request identifier (int or str). Omitted for notifications.
            When omitted, no response is expected.
    """

    jsonrpc: str = Field(..., description="JSON-RPC version (must be '2.0')")
    method: str = Field(..., description="Method name (required, non-empty)")
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Method parameters (optional)",
    )
    id: Optional[Union[int, str]] = Field(
        default=None,
        description="Request ID (optional, omit for notifications)",
    )

    @field_validator("jsonrpc")
    @classmethod
    def validate_jsonrpc_version(cls, v: str) -> str:
        """Validate that jsonrpc is exactly '2.0'."""
        if v != "2.0":
            raise ValueError("jsonrpc must be '2.0'")
        return v

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        """Validate that method is a non-empty string."""
        if not v or not isinstance(v, str):
            raise ValueError("method must be a non-empty string")
        return v


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 response object.

    Represents a JSON-RPC 2.0 response from a method call.
    Either contains a result (success) or error (failure), not both.

    Attributes:
        jsonrpc: JSON-RPC protocol version (always "2.0").
        result: Result of successful method call. Omitted if error.
        error: Error object if method call failed. Omitted if result.
        id: Request ID matching the request that triggered this response.
            Null for error responses to invalid requests.
    """

    jsonrpc: str = Field(
        default="2.0",
        description="JSON-RPC version (always '2.0')",
    )
    result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Result of successful method call (success case)",
    )
    error: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Error object if method call failed (error case)",
    )
    id: Optional[Union[int, str]] = Field(
        default=None,
        description="Request ID from corresponding request",
    )
