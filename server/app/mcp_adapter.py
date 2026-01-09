"""MCP (Model Context Protocol) adapter for Gemini-CLI integration."""

from typing import List

from .models import MCPManifest, MCPTool
from .plugin_loader import PluginManager


class MCPAdapter:
    """Adapts vision server capabilities to MCP format."""

    def __init__(self, plugin_manager: PluginManager, base_url: str = ""):
        self.plugin_manager = plugin_manager
        self.base_url = base_url.rstrip("/")

    def get_manifest(self) -> dict:
        """Generate MCP manifest for Gemini-CLI discovery."""
        tools = self._build_tools()

        manifest = MCPManifest(
            tools=tools,
            server={
                "name": "forgesyte",
                "version": "0.1.0",
                "description": "ForgeSyte: A vision core for engineered systems",
            },
            version="1.0",
        )

        return manifest.model_dump()

    def _build_tools(self) -> List[MCPTool]:
        """Build tool list from registered plugins."""
        tools = []

        for name, meta in self.plugin_manager.list().items():
            tool = MCPTool(
                id=f"vision.{name}",
                title=meta.get("name", name),
                description=meta.get("description", f"Analyze image using {name}"),
                inputs=meta.get("inputs", ["image"]),
                outputs=meta.get("outputs", ["json"]),
                invoke_endpoint=f"{self.base_url}/v1/analyze?plugin={name}",
                permissions=meta.get("permissions", []),
            )
            tools.append(tool)

        # Add built-in tools
        tools.append(
            MCPTool(
                id="vision.list_plugins",
                title="List Vision Plugins",
                description="List all available vision analysis plugins",
                inputs=[],
                outputs=["json"],
                invoke_endpoint=f"{self.base_url}/v1/plugins",
                permissions=[],
            )
        )

        tools.append(
            MCPTool(
                id="vision.job_status",
                title="Check Job Status",
                description="Check the status of an analysis job",
                inputs=["job_id"],
                outputs=["json"],
                invoke_endpoint=f"{self.base_url}/v1/jobs/{{job_id}}",
                permissions=[],
            )
        )

        return tools

    def invoke_tool(self, tool_id: str, params: dict) -> dict:
        """Handle tool invocation from MCP client."""
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
