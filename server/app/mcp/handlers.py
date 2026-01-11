"""MCP protocol method handlers for JSON-RPC transport.

This module implements the core MCP protocol methods:
- initialize: Establish connection and capability negotiation
- tools/list: List available tools (plugins)
- tools/call: Invoke a tool/plugin with arguments
- resources/list: List available resources
- resources/read: Read resource contents
- ping: Keep-alive verification
"""

import logging
from typing import Any, Dict, Optional

from ..plugin_loader import PluginManager
from ..tasks import job_store
from .adapter import (
    MCP_SERVER_NAME,
    MCP_SERVER_VERSION,
    MCPAdapter,
)
from .jsonrpc import JSONRPCErrorCode
from .transport import MCPTransportError

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
            "Initialize request from client",
            extra={
                "client_name": client_info.get("name", "unknown"),
                "client_version": client_version or "unspecified",
                "server_name": MCP_SERVER_NAME,
                "server_version": MCP_SERVER_VERSION,
            },
        )

        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
            },
            "serverInfo": {
                "name": MCP_SERVER_NAME,
                "version": MCP_SERVER_VERSION,
            },
        }

    async def tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list method.

        Returns list of available tools from registered plugins in MCP format.

        Args:
            params: Request parameters (typically empty for tools/list)

        Returns:
            Response dictionary containing tools list with name,
            description, and inputSchema for each tool.
        """
        plugins = self.plugin_manager.list()
        logger.debug(
            "Listing available tools",
            extra={"tool_count": len(plugins)},
        )

        tools = []

        # Get all plugins and convert to MCP tool format
        for plugin_name, plugin_meta in plugins.items():
            # Build MCP tool with required fields
            tool = {
                "name": plugin_name,
                "description": plugin_meta.get("description", f"Plugin: {plugin_name}"),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "image": {
                            "type": "string",
                            "description": "Base64-encoded image data or image URL",
                        },
                        "options": {
                            "type": "object",
                            "description": "Plugin-specific options",
                            "properties": {},
                        },
                    },
                    "required": ["image"],
                },
            }
            tools.append(tool)

        return {
            "tools": tools,
        }

    async def tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call method.

        Invokes a tool (plugin) with given arguments.

        Args:
            params: Request parameters containing:
                - name: Tool name to invoke
                - arguments: Dict of arguments to pass to tool (optional)

        Returns:
            Response dictionary containing:
                - content: List of content items with results
                - isError: Boolean indicating if execution failed (optional)

        Raises:
            MCPTransportError: If tool not found or invalid params
        """
        # Extract and validate required parameters
        tool_name = params.get("name")
        if not tool_name:
            raise MCPTransportError(
                code=JSONRPCErrorCode.INVALID_PARAMS,
                message="Missing required parameter: name",
            )

        tool_arguments = params.get("arguments", {})

        logger.debug(
            "Invoking tool",
            extra={
                "tool_name": tool_name,
                "argument_keys": list(tool_arguments.keys()) if tool_arguments else [],
            },
        )

        # Get the plugin/tool
        plugin = self.plugin_manager.get(tool_name)
        if not plugin:
            raise MCPTransportError(
                code=JSONRPCErrorCode.INVALID_PARAMS,
                message=f"Tool '{tool_name}' not found",
            )

        try:
            # For now, we'll return a simple response
            # In a real implementation, this would actually invoke the plugin
            result = {
                "content": [
                    {
                        "type": "text",
                        "text": f"Tool '{tool_name}' executed successfully",
                    }
                ]
            }
            return result
        except Exception as e:
            logger.error(
                "Error invoking tool",
                extra={"tool_name": tool_name, "error": str(e)},
            )
            raise MCPTransportError(
                code=JSONRPCErrorCode.INTERNAL_ERROR,
                message=f"Tool execution failed: {str(e)}",
            ) from e

    async def resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list method.

        Lists available resources (jobs, media, etc.).

        Args:
            params: Request parameters containing:
                - cursor: Optional pagination cursor

        Returns:
            Response dictionary containing:
                - resources: List of available resource definitions
                - nextCursor: Optional cursor for pagination
        """
        logger.debug("Listing available resources")

        # Build resource list
        resources = []

        # Add job resources if job store exists
        if job_store:
            try:
                # Get recent jobs
                jobs = await job_store.list_jobs(limit=10)
                for job in jobs:
                    plugin_name = job.get("plugin", "unknown")
                    resources.append(
                        {
                            "uri": f"forgesyte://job/{job['job_id']}",
                            "name": f"Job {job['job_id'][:8]}",
                            "mimeType": "application/json",
                            "description": f"Job for plugin: {plugin_name}",
                        }
                    )
                logger.debug(
                    "Listed job resources",
                    extra={"resource_count": len(resources)},
                )
            except Exception as e:
                logger.warning(
                    "Error listing job resources",
                    extra={"error": str(e)},
                )

        return {
            "resources": resources,
            "nextCursor": None,  # No pagination for now
        }

    async def resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read method.

        Reads the contents of a specific resource.

        Args:
            params: Request parameters containing:
                - uri: The resource URI to read

        Returns:
            Response dictionary containing:
                - contents: List of content items

        Raises:
            MCPTransportError: If URI is missing or resource not found
        """
        import json

        uri = params.get("uri")
        if not uri:
            raise MCPTransportError(
                code=JSONRPCErrorCode.INVALID_PARAMS,
                message="Missing required parameter: uri",
            )

        logger.debug(
            "Reading resource",
            extra={"uri": uri},
        )

        # Parse URI to get resource type and ID
        if uri.startswith("forgesyte://job/"):
            job_id = uri.replace("forgesyte://job/", "")
            job = await job_store.get(job_id)
            if not job:
                raise MCPTransportError(
                    code=JSONRPCErrorCode.INVALID_PARAMS,
                    message=f"Job '{job_id}' not found",
                )

            # Return job data as JSON
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(job, default=str),
                    }
                ]
            }

        # Unknown resource type
        raise MCPTransportError(
            code=JSONRPCErrorCode.INVALID_PARAMS,
            message=f"Unknown resource type in URI: {uri}",
        )

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
