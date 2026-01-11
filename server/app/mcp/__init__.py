"""MCP (Model Context Protocol) implementation module."""

from .adapter import (
    MCP_PROTOCOL_VERSION,
    MCP_SERVER_NAME,
    MCP_SERVER_VERSION,
    MCPAdapter,
    MCPServerInfo,
    MCPToolSchema,
    build_gemini_extension_manifest,
    negotiate_mcp_version,
)
from .handlers import MCPProtocolHandlers
from .jsonrpc import JSONRPCError, JSONRPCErrorCode, JSONRPCRequest, JSONRPCResponse
from .routes import router
from .transport import MCPTransport, MCPTransportError

__all__ = [
    "MCP_PROTOCOL_VERSION",
    "MCP_SERVER_NAME",
    "MCP_SERVER_VERSION",
    "MCPAdapter",
    "MCPServerInfo",
    "MCPToolSchema",
    "build_gemini_extension_manifest",
    "negotiate_mcp_version",
    "MCPProtocolHandlers",
    "JSONRPCError",
    "JSONRPCErrorCode",
    "JSONRPCRequest",
    "JSONRPCResponse",
    "router",
    "MCPTransport",
    "MCPTransportError",
]
