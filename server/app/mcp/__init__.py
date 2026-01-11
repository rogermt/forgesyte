"""MCP (Model Context Protocol) implementation module.

This module provides the complete MCP server implementation for ForgeSyte,
enabling client discovery and tool invocation via the Model Context Protocol.

Core Components:
- adapter: MCPAdapter for converting plugins to MCP tools and managing manifests
- jsonrpc: JSON-RPC 2.0 protocol implementation for message transport
- handlers: Protocol message handlers for client requests
- routes: HTTP routes for MCP endpoints
- transport: HTTP transport layer for MCP communication

Usage:
    from server.app.mcp import MCPAdapter, MCPProtocolHandlers, router

    # Initialize adapter with plugin manager
    adapter = MCPAdapter(plugin_manager, base_url="http://localhost:8000")

    # Get MCP manifest for client discovery
    manifest = adapter.get_manifest()
"""

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
