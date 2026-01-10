"""MCP protocol method handlers for JSON-RPC transport.

This module implements the core MCP protocol methods:
- initialize: Establish connection and capability negotiation
- tools/list: List available tools (plugins)
- ping: Keep-alive verification
"""

import logging
from typing import Any, Dict, Optional

from .mcp_adapter import (
    MCP_PROTOCOL_VERSION,
    MCP_SERVER_NAME,
    MCP_SERVER_VERSION,
    MCPAdapter,
)
from .plugin_loader import PluginManager

logger = logging.getLogger(__name__)


class MCPProtocolHandlers:
    """Handles MCP protocol method calls."""

    def __init__(
        self,
        plugin_manager: PluginManager,
        mcp_adapter: Optional[MCPAdapter] = None,
    ) -> None:
        """Initialize protocol handlers.

        Args:
            plugin_manager: PluginManager instance for tool discovery
            mcp_adapter: Optional MCPAdapter for manifest generation
        """
        self.plugin_manager = plugin_manager
        self.mcp_adapter = mcp_adapter or MCPAdapter(plugin_manager)

    async def initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize method.

        Establishes the connection and negotiates capabilities with the client.

        Args:
            params: Request parameters containing:
                - clientInfo: Client metadata (name, version)
                - protocolVersion: Client's MCP protocol version

        Returns:
            Response dictionary containing:
                - serverInfo: Server metadata
                - capabilities: Server's protocol capabilities
        """
        # Extract client info from params (optional)
        client_info = params.get("clientInfo", {})
        client_version = params.get("protocolVersion")

        logger.info(
            f"Initialize request from client: {client_info.get('name', 'unknown')} "
            f"(protocol: {client_version or 'unspecified'})"
        )

        return {
            "serverInfo": {
                "name": MCP_SERVER_NAME,
                "version": MCP_SERVER_VERSION,
                "protocolVersion": MCP_PROTOCOL_VERSION,
            },
            "capabilities": {
                "tools": True,  # Server supports tools/list and tools/call
            },
        }

    async def tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list method.

        Returns list of available tools from registered plugins.

        Args:
            params: Request parameters (typically empty for tools/list)

        Returns:
            Response dictionary containing:
                - tools: List of available tool definitions
        """
        logger.debug("Listing available tools")

        # Get manifest from adapter, which includes all tools
        manifest = self.mcp_adapter.get_manifest()

        # Return tools array
        return {
            "tools": manifest.get("tools", []),
        }

    async def ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping method.

        Keep-alive and basic server verification.

        Args:
            params: Request parameters (typically empty)

        Returns:
            Response dictionary containing:
                - status: "pong" to indicate server is alive
        """
        logger.debug("Ping request")

        return {
            "status": "pong",
        }
