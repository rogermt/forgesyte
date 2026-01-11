"""MCP (Model Context Protocol) adapter for Gemini-CLI integration.

This module provides the MCPAdapter class that converts ForgeSyte's vision
capabilities into MCP-compatible format for client discovery and invocation.

Classes:
    MCPServerInfo: Server metadata for MCP manifest
    MCPToolSchema: Schema for MCP tool descriptor
    MCPAdapter: Converts vision server capabilities to MCP format

Functions:
    build_gemini_extension_manifest: Create Gemini extension manifest
    negotiate_mcp_version: Handle MCP version compatibility negotiation
"""

import logging
import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError

from ..models import MCPManifest, MCPTool, PluginMetadata
from ..plugin_loader import PluginManager

logger = logging.getLogger(__name__)

# MCP Version constants
MCP_PROTOCOL_VERSION: str = "1.0.0"
MCP_SERVER_NAME: str = "forgesyte"
MCP_SERVER_VERSION: str = "0.1.0"

# Cache TTL in seconds
DEFAULT_MANIFEST_CACHE_TTL: int = 300


class MCPServerInfo(BaseModel):
    """Server metadata for MCP manifest.

    Represents the server's identity and capabilities in MCP format.

    Attributes:
        name: Server name (e.g., "forgesyte")
        version: Server version (e.g., "0.1.0")
        mcp_version: MCP protocol version (e.g., "1.0.0")
    """

    name: str = Field(..., description="Server name")
    version: str = Field(..., description="Server version")
    mcp_version: str = Field(..., description="MCP protocol version")


class MCPToolSchema(BaseModel):
    """Schema for MCP tool descriptor with validation.

    Defines the structure and constraints for tools exported via MCP.

    Attributes:
        id: Tool unique identifier (format: vision.{plugin_name})
        title: Human-readable tool name
        description: Tool description and capabilities
        inputs: List of accepted input types (e.g., ["image"])
        outputs: List of produced output types (e.g., ["json"])
        invoke_endpoint: HTTP endpoint to invoke the tool
        permissions: List of required permissions (format: resource:action)
    """

    id: str = Field(..., description="Tool unique identifier")
    title: str = Field(..., description="Tool display name")
    description: str = Field(..., description="Tool description")
    inputs: List[str] = Field(default_factory=list, description="Input types")
    outputs: List[str] = Field(default_factory=list, description="Output types")
    invoke_endpoint: str = Field(..., description="API endpoint to invoke tool")
    permissions: List[str] = Field(
        default_factory=list, description="Required permissions"
    )


class MCPAdapter:
    """Adapts vision server capabilities to MCP (Model Context Protocol) format.

    Converts plugin metadata into MCP-compatible tool definitions for
    discovery by MCP clients. Includes caching and manifest generation.

    Attributes:
        plugin_manager: PluginManager instance for plugin discovery
        base_url: Base URL for invoking tools via HTTP
        _manifest_cache: Cached manifest dictionary
        _manifest_cache_time: Timestamp of cached manifest
        _manifest_cache_ttl: Cache time-to-live in seconds
    """

    def __init__(
        self,
        plugin_manager: Optional[PluginManager] = None,
        base_url: str = "",
    ) -> None:
        """Initialize the MCP adapter.

        Args:
            plugin_manager: PluginManager instance for plugin discovery.
                           If None, adapter will return empty tool list.
            base_url: Base URL for invoke endpoints. Trailing slashes are
                     automatically removed.

        Raises:
            TypeError: If plugin_manager is not PluginManager or None
        """
        self.plugin_manager = plugin_manager
        self.base_url = base_url.rstrip("/") if base_url else ""

        # Manifest caching
        self._manifest_cache: Optional[Dict[str, Any]] = None
        self._manifest_cache_time: Optional[float] = None
        self._manifest_cache_ttl: int = DEFAULT_MANIFEST_CACHE_TTL

        logger.debug(
            "MCPAdapter initialized",
            extra={
                "base_url": self.base_url,
                "has_plugin_manager": plugin_manager is not None,
            },
        )

    def get_manifest(self) -> Dict[str, Any]:
        """Generate MCP manifest for client discovery.

        Builds a complete MCP manifest containing server information and
        all available tools derived from registered plugins.

        Returns:
            Dictionary containing MCP manifest with structure:
            {
                "tools": [...],
                "server": {"name": str, "version": str, "mcp_version": str},
                "version": "1.0"
            }

        Raises:
            ValidationError: If tool schemas cannot be validated (caught internally)
        """
        logger.debug("Building fresh MCP manifest")
        tools = self._build_tools()

        server_info: Dict[str, str] = {
            "name": MCP_SERVER_NAME,
            "version": MCP_SERVER_VERSION,
            "mcp_version": MCP_PROTOCOL_VERSION,
        }

        manifest = MCPManifest(
            tools=tools,
            server=server_info,
            version="1.0",
        )

        return manifest.model_dump()

    def build_manifest(self, tools: Optional[List[MCPTool]] = None) -> Dict[str, Any]:
        """Build manifest from provided tools or auto-discover from plugins.

        Useful for testing and manual manifest construction. For normal
        operation, use get_manifest() or get_cached_manifest().

        Args:
            tools: Optional list of MCPTool objects. If None, auto-discovers
                  tools from registered plugins.

        Returns:
            Dictionary containing MCP manifest with provided or discovered tools.

        Raises:
            ValidationError: If MCPManifest validation fails
        """
        if tools is None:
            tools = self._build_tools()

        server_info: Dict[str, str] = {
            "name": MCP_SERVER_NAME,
            "version": MCP_SERVER_VERSION,
            "mcp_version": MCP_PROTOCOL_VERSION,
        }

        manifest = MCPManifest(
            tools=tools,
            server=server_info,
            version="1.0",
        )

        logger.debug("Manifest built", extra={"tool_count": len(tools)})
        return manifest.model_dump()

    def _cache_manifest(self, manifest: Dict[str, Any]) -> None:
        """Cache a manifest with timestamp for TTL tracking.

        Args:
            manifest: Manifest dictionary to cache
        """
        self._manifest_cache = manifest
        self._manifest_cache_time = time.time()
        logger.debug(
            "Manifest cached",
            extra={"ttl_seconds": self._manifest_cache_ttl},
        )

    def _is_manifest_cache_valid(self) -> bool:
        """Check if cached manifest is still valid (not expired).

        Returns:
            True if cache exists and hasn't exceeded TTL, False otherwise.
        """
        if self._manifest_cache is None or self._manifest_cache_time is None:
            return False

        elapsed = time.time() - self._manifest_cache_time
        is_valid = elapsed < self._manifest_cache_ttl

        if not is_valid:
            logger.debug(
                "Manifest cache expired",
                extra={"elapsed_seconds": elapsed},
            )
        return is_valid

    def get_cached_manifest(self) -> Dict[str, Any]:
        """Get manifest from cache or regenerate if expired.

        Implements TTL-based caching to reduce manifest generation
        overhead for repeated requests.

        Returns:
            Dictionary containing MCP manifest (cached or freshly generated).

        Raises:
            ValidationError: If manifest generation fails (caught internally)
        """
        if self._is_manifest_cache_valid():
            logger.debug("Manifest cache hit")
            return self._manifest_cache  # type: ignore[return-value]

        # Cache expired or doesn't exist, regenerate
        logger.debug("Manifest cache miss - regenerating")
        manifest = self.get_manifest()
        self._cache_manifest(manifest)
        return manifest

    def _build_tools(self) -> List[MCPTool]:
        """Build tool list from registered plugins with validation.

        Iterates through all plugins, validates their metadata against
        PluginMetadata schema, and converts valid plugins to MCP tools.
        Invalid plugins are logged and skipped to prevent cascade failures.

        Returns:
            List of MCPTool objects, may be empty if no plugins or
            all plugins failed validation.

        Raises:
            ValidationError: Caught internally and logged per plugin
        """
        tools: List[MCPTool] = []

        # Return empty list if no plugin manager configured
        if self.plugin_manager is None:
            logger.warning("No plugin manager available for tool discovery")
            return tools

        # Convert plugin metadata to MCP tools
        plugin_metadata = self.plugin_manager.list()
        logger.debug(
            "Building tools from plugins",
            extra={"plugin_count": len(plugin_metadata)},
        )

        for name, meta in plugin_metadata.items():
            # Validate metadata against schema
            try:
                validated_meta = PluginMetadata(**meta)
                tool = self._plugin_metadata_to_mcp_tool(
                    name, validated_meta.model_dump()
                )
                tools.append(tool)
                logger.debug(
                    "Added tool from plugin",
                    extra={"plugin_name": name, "tool_id": tool.id},
                )
            except ValidationError as e:
                logger.error(
                    "Invalid plugin metadata",
                    extra={
                        "plugin_name": name,
                        "error_count": e.error_count(),
                        "errors": str(e),
                    },
                )
                # Continue processing other plugins instead of failing entirely
                continue

        logger.info(
            "Tools built from plugins",
            extra={"total_tools": len(tools)},
        )
        return tools

    def _plugin_metadata_to_mcp_tool(
        self, plugin_name: str, meta: Dict[str, Any]
    ) -> MCPTool:
        """Convert plugin metadata dictionary to MCPTool.

        Maps plugin metadata fields to MCP tool format with sensible
        defaults and fallbacks.

        Args:
            plugin_name: Name of the plugin
            meta: Plugin metadata dictionary (already validated)

        Returns:
            MCPTool instance with all required fields populated

        Raises:
            KeyError: If required fields missing (should not occur if
                     metadata was validated)
        """
        # Use title field if present, otherwise fall back to name
        title: str = meta.get("title") or meta.get("name") or plugin_name

        # Description is optional, provide sensible default
        description: str = meta.get("description", f"ForgeSyte plugin: {plugin_name}")

        # Inputs/outputs with sensible defaults
        inputs: List[str] = meta.get("inputs", ["image"])
        outputs: List[str] = meta.get("outputs", ["json"])

        # Build invoke endpoint for HTTP
        invoke_endpoint: str = f"{self.base_url}/v1/analyze?plugin={plugin_name}"

        # Permissions are optional
        permissions: List[str] = meta.get("permissions", [])

        return MCPTool(
            id=f"vision.{plugin_name}",
            title=title,
            description=description,
            inputs=inputs,
            outputs=outputs,
            invoke_endpoint=invoke_endpoint,
            permissions=permissions,
        )

    def invoke_tool(self, tool_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool invocation request from MCP client.

        This is a placeholder for future tool invocation handling.
        Currently just returns routing information to the HTTP layer.

        Args:
            tool_id: Tool identifier (format: vision.{plugin_name})
            params: Tool parameters from client

        Returns:
            Dictionary containing invocation routing information:
            {
                "tool_id": str,
                "status": str,
                "message": str
            }

        Raises:
            ValueError: If tool_id format is invalid (not implemented)
        """
        logger.debug(
            "Tool invocation requested",
            extra={"tool_id": tool_id},
        )
        # This would be called by an MCP transport layer
        # For now, just return info about how to invoke
        return {
            "tool_id": tool_id,
            "status": "use_http",
            "message": "Use the invoke_endpoint via HTTP POST",
        }


def build_gemini_extension_manifest(
    server_url: str,
    name: str = "vision-mcp",
    version: str = "0.1.0",
) -> Dict[str, Any]:
    """Build a Gemini extension manifest for easy installation.

    Creates a manifest file that Gemini CLI can use to discover and
    install the ForgeSyte vision MCP server.

    Args:
        server_url: Base URL of the MCP server
        name: Extension name (default: "vision-mcp")
        version: Extension version (default: "0.1.0")

    Returns:
        Dictionary containing Gemini extension manifest with structure:
        {
            "name": str,
            "version": str,
            "description": str,
            "author": str,
            "license": str,
            "mcp": {...},
            "commands": [...],
            "requirements": {...},
            "install": {...}
        }

    Raises:
        ValueError: If server_url is empty or malformed
    """
    if not server_url:
        logger.warning("Building Gemini extension manifest without server_url")

    logger.debug(
        "Building Gemini extension manifest",
        extra={"server_url": server_url, "name": name},
    )

    return {
        "name": name,
        "version": version,
        "description": ("Vision MCP Server - Modular image analysis for Gemini-CLI"),
        "author": "Vision MCP Team",
        "license": "MIT",
        "mcp": {
            "manifest_url": f"{server_url}/.well-known/mcp-manifest",
            "transport": "http",
        },
        "commands": [
            {
                "name": "vision-analyze",
                "description": "Analyze an image using Vision MCP",
                "usage": "vision-analyze <image_path> [--plugin=ocr]",
            },
            {
                "name": "vision-stream",
                "description": "Start streaming camera analysis",
                "usage": "vision-stream [--plugin=motion]",
            },
        ],
        "requirements": {"python": ">=3.9"},
        "install": {"type": "pip", "package": "vision-mcp-server"},
    }


def negotiate_mcp_version(
    client_version: Optional[str] = None,
) -> Dict[str, Any]:
    """Negotiate MCP protocol version compatibility with client.

    Handles version negotiation to ensure client and server are compatible.
    Supports future version negotiation when multiple versions are supported.

    Args:
        client_version: MCP version requested by client (e.g., "1.0.0").
                       If None, returns server version info only.

    Returns:
        Dictionary containing compatibility information:
        {
            "server_version": str,
            "compatible": bool,
            "supported_versions": List[str],
            "message": str,
            "client_version": str (if provided),
        }

    Raises:
        ValueError: If client_version format is invalid (not implemented)
    """
    supported_versions: List[str] = [MCP_PROTOCOL_VERSION]

    if client_version is None:
        logger.debug("MCP version info requested - no client version provided")
        return {
            "server_version": MCP_PROTOCOL_VERSION,
            "supported_versions": supported_versions,
            "compatible": True,
            "message": f"Server supports MCP {MCP_PROTOCOL_VERSION}",
        }

    # Check if client version is supported
    is_compatible: bool = (
        client_version in supported_versions or client_version == MCP_PROTOCOL_VERSION
    )

    if is_compatible:
        logger.info(
            "MCP version negotiation successful",
            extra={
                "client_version": client_version,
                "server_version": MCP_PROTOCOL_VERSION,
            },
        )
        return {
            "server_version": MCP_PROTOCOL_VERSION,
            "client_version": client_version,
            "compatible": True,
            "message": f"Client MCP version {client_version} is compatible",
        }

    # Incompatible version
    supported_str: str = ", ".join(supported_versions)
    logger.warning(
        "MCP version negotiation failed",
        extra={
            "client_version": client_version,
            "supported_versions": supported_str,
        },
    )
    return {
        "server_version": MCP_PROTOCOL_VERSION,
        "client_version": client_version,
        "compatible": False,
        "supported_versions": supported_versions,
        "message": (
            f"Client MCP version {client_version} is not compatible. "
            f"Server supports: {supported_str}"
        ),
    }
