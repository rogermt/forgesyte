"""MCP protocol method handlers for JSON-RPC transport.

This module implements the core MCP protocol methods:
- initialize: Establish connection and capability negotiation
- tools/list: List available tools (plugins)
- tools/call: Invoke a tool/plugin with arguments
- resources/list: List available resources
- resources/read: Read resource contents
- ping: Keep-alive verification
"""

import base64
import inspect
import json
import logging
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel

from ..plugin_loader import PluginRegistry
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
        plugin_manager: PluginRegistry,
        mcp_adapter: Optional[MCPAdapter] = None,
    ) -> None:
        """Initialize protocol handlers.

        Args:
            plugin_manager: PluginRegistry instance for tool discovery
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

        for plugin_name, plugin_meta in plugins.items():
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
        Supports image input as: URL (http/https), base64 string, or data URL.

        Args:
            params: Request parameters containing:
                - name: Tool name to invoke
                - arguments: Dict of arguments to pass to tool (optional)

        Returns:
            Response dictionary containing:
                - content: List of content items with results

        Raises:
            MCPTransportError: If tool not found or invalid params
        """
        # Validate required params
        tool_name = params.get("name")
        if not tool_name:
            raise MCPTransportError(
                code=JSONRPCErrorCode.INVALID_PARAMS,
                message="Missing required parameter: name",
            )

        tool_arguments = params.get("arguments") or {}
        image = tool_arguments.get("image")
        options = tool_arguments.get("options") or {}

        if not image:
            raise MCPTransportError(
                code=JSONRPCErrorCode.INVALID_PARAMS,
                message="Missing required argument: image",
            )

        # Load plugin
        plugin = self.plugin_manager.get(tool_name)
        if not plugin:
            raise MCPTransportError(
                code=JSONRPCErrorCode.INVALID_PARAMS,
                message=f"Tool '{tool_name}' not found",
            )

        try:
            # Convert image to bytes
            image_bytes: bytes

            if isinstance(image, (bytes, bytearray)):
                image_bytes = bytes(image)
            elif isinstance(image, str):
                # Check if URL - fetch the image
                if image.startswith(("http://", "https://")):
                    logger.debug(
                        "Fetching image from URL",
                        extra={"url": image[:100]},
                    )
                    try:
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            resp = await client.get(image)
                            resp.raise_for_status()
                            image_bytes = resp.content
                        logger.debug(
                            "Image fetched successfully",
                            extra={"size": len(image_bytes)},
                        )
                    except httpx.HTTPStatusError as e:
                        raise MCPTransportError(
                            code=JSONRPCErrorCode.INVALID_PARAMS,
                            message=(
                                f"Failed to fetch image: HTTP {e.response.status_code}"
                            ),
                        ) from e
                    except httpx.RequestError as e:
                        raise MCPTransportError(
                            code=JSONRPCErrorCode.INVALID_PARAMS,
                            message=f"Failed to fetch image: {type(e).__name__}: {e}",
                        ) from e
                # Check if data URL
                elif image.startswith("data:") and "base64," in image:
                    b64_part = image.split("base64,", 1)[1]
                    try:
                        image_bytes = base64.b64decode(b64_part, validate=True)
                    except Exception as e:
                        raise MCPTransportError(
                            code=JSONRPCErrorCode.INVALID_PARAMS,
                            message=f"Invalid base64 in data URL: {e}",
                        ) from e
                # Try base64 decode
                else:
                    try:
                        image_bytes = base64.b64decode(image, validate=True)
                    except Exception:
                        # Last resort: encode as UTF-8 bytes
                        image_bytes = image.encode("utf-8")
            else:
                raise MCPTransportError(
                    code=JSONRPCErrorCode.INVALID_PARAMS,
                    message="Invalid argument: image must be string or bytes",
                )

            # Invoke plugin via run_tool
            tool_name = options.get("tool", "default") if isinstance(options, dict) else "default"
            tool_args = {"image": image_bytes, "options": options or {}}
            if hasattr(plugin, "run_tool") and callable(plugin.run_tool):
                maybe_coro = plugin.run_tool(tool_name, tool_args)
                if inspect.isawaitable(maybe_coro):
                    result = await maybe_coro
                else:
                    result = maybe_coro
            else:
                raise MCPTransportError(
                    code=JSONRPCErrorCode.INTERNAL_ERROR,
                    message="Plugin does not have run_tool method",
                )

            # Convert Pydantic models to dict
            if isinstance(result, BaseModel):
                result = result.model_dump()

            # Serialize to JSON string
            try:
                result_text = json.dumps(result, ensure_ascii=False)
            except (TypeError, ValueError) as e:
                raise MCPTransportError(
                    code=JSONRPCErrorCode.INTERNAL_ERROR,
                    message=f"Plugin result is not JSON-serializable: {e}",
                ) from e

            # Return MCP content format
            return {
                "content": [
                    {
                        "type": "text",
                        "text": result_text,
                    }
                ]
            }

        except MCPTransportError:
            raise
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

        resources = []

        if job_store:
            try:
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
            "nextCursor": None,
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

        if uri.startswith("forgesyte://job/"):
            job_id = uri.replace("forgesyte://job/", "")
            job = await job_store.get(job_id)
            if not job:
                raise MCPTransportError(
                    code=JSONRPCErrorCode.INVALID_PARAMS,
                    message=f"Job '{job_id}' not found",
                )

            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(job, default=str),
                    }
                ]
            }

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
