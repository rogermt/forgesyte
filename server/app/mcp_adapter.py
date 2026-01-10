"""MCP (Model Context Protocol) adapter for Gemini-CLI integration."""

import logging
from typing import Any, Dict, List

from pydantic import BaseModel, Field, ValidationError

from .models import MCPManifest, MCPTool, PluginMetadata
from .plugin_loader import PluginManager

logger = logging.getLogger(__name__)

# MCP Version constant
MCP_PROTOCOL_VERSION = "1.0.0"
MCP_SERVER_NAME = "forgesyte"
MCP_SERVER_VERSION = "0.1.0"


class MCPServerInfo(BaseModel):
    """Server metadata for MCP manifest."""

    name: str = Field(..., description="Server name")
    version: str = Field(..., description="Server version")
    mcp_version: str = Field(..., description="MCP protocol version")


class MCPToolSchema(BaseModel):
    """Schema for MCP tool descriptor with validation."""

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
    """Adapts vision server capabilities to MCP format."""

    def __init__(self, plugin_manager: PluginManager, base_url: str = ""):
        """Initialize MCPAdapter.

        Args:
            plugin_manager: PluginManager instance for plugin discovery
            base_url: Base URL for invoke endpoints (trailing slash removed)
        """
        self.plugin_manager = plugin_manager
        self.base_url = base_url.rstrip("/") if base_url else ""

    def get_manifest(self) -> dict:
        """Generate MCP manifest for Gemini-CLI discovery.

        Returns:
            Dictionary containing MCP manifest with server info and tools.
        """
        tools = self._build_tools()

        server_info = {
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

    def _build_tools(self) -> List[MCPTool]:
        """Build tool list from registered plugins.

        Validates each plugin's metadata against the PluginMetadata schema.
        Invalid plugins are logged and skipped.

        Returns:
            List of MCPTool objects converted from plugin metadata.
        """
        tools: List[MCPTool] = []

        # Convert plugin metadata to MCP tools
        for name, meta in self.plugin_manager.list().items():
            # Validate metadata against schema
            try:
                validated_meta = PluginMetadata(**meta)
                tool = self._plugin_metadata_to_mcp_tool(
                    name, validated_meta.model_dump()
                )
                tools.append(tool)
            except ValidationError as e:
                logger.error(
                    f"Invalid plugin metadata for '{name}': "
                    f"{e.error_count()} error(s) - {e}"
                )
                # Continue processing other plugins instead of failing entirely
                continue

        return tools

    def _plugin_metadata_to_mcp_tool(
        self, plugin_name: str, meta: Dict[str, Any]
    ) -> MCPTool:
        """Convert plugin metadata to MCPTool.

        Args:
            plugin_name: Name of the plugin
            meta: Plugin metadata dictionary

        Returns:
            MCPTool instance
        """
        # Use title field if present, otherwise fall back to name
        title = meta.get("title") or meta.get("name") or plugin_name

        # Description is optional, provide fallback
        description = meta.get("description", f"ForgeSyte plugin: {plugin_name}")

        # Inputs/outputs with sensible defaults
        inputs = meta.get("inputs", ["image"])
        outputs = meta.get("outputs", ["json"])

        # Build invoke endpoint
        invoke_endpoint = f"{self.base_url}/v1/analyze?plugin={plugin_name}"

        # Permissions are optional
        permissions = meta.get("permissions", [])

        return MCPTool(
            id=f"vision.{plugin_name}",
            title=title,
            description=description,
            inputs=inputs,
            outputs=outputs,
            invoke_endpoint=invoke_endpoint,
            permissions=permissions,
        )

    def invoke_tool(self, tool_id: str, params: dict) -> dict:
        """Handle tool invocation from MCP client.

        Args:
            tool_id: Tool identifier
            params: Tool parameters

        Returns:
            Dictionary with invocation information
        """
        # This would be called by an MCP transport layer
        # For now, just return info about how to invoke
        return {
            "tool_id": tool_id,
            "status": "use_http",
            "message": "Use the invoke_endpoint via HTTP POST",
        }


def build_gemini_extension_manifest(
    server_url: str, name: str = "vision-mcp", version: str = "0.1.0"
) -> dict:
    """Build a Gemini extension manifest for easy installation."""
    return {
        "name": name,
        "version": version,
        "description": "Vision MCP Server - Modular image analysis for Gemini-CLI",
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
