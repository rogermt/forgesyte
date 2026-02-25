"""Tool resolution service for plugin-agnostic capability matching.

This module handles the resolution of logical tool IDs (from UI) to actual
plugin tool IDs based on file type and tool capabilities.

The backend remains completely plugin-agnostic:
- No hardcoded tool names
- No naming convention assumptions
- No prefix or substring matching on tool IDs
- Plugin manifest is the only source of truth
- Capabilities are the semantic bridge
"""

from typing import Any

from app.services.plugin_management_service import PluginManagementService


def resolve_tool(
    logical_tool_id: str,
    file_mime: str,
    plugin_name: str,
    plugin_service: PluginManagementService | None = None,
) -> str:
    """Resolve a logical tool ID to an actual plugin tool ID.

    Args:
        logical_tool_id: Capability string from UI (e.g., "player_detection")
        file_mime: MIME type of uploaded file (e.g., "video/mp4", "image/png")
        plugin_name: Name of the plugin to search in
        plugin_service: PluginManagementService instance (for dependency injection)

    Returns:
        The actual plugin tool ID (e.g., "video_player_tracking")

    Raises:
        ValueError: If no matching tool found in plugin manifest

    Architecture:
        1. Load plugin manifest (source of truth)
        2. Determine required input type from file MIME
        3. Find tools matching:
           - logical_tool_id in tool.capabilities
           - required_input_type in tool.input_types
        4. Return first matching tool ID
    """
    if plugin_service is None:
        raise ValueError("plugin_service is required")

    manifest: dict[str, Any] | None = plugin_service.get_plugin_manifest(plugin_name)
    if not manifest:
        raise ValueError(f"Plugin '{plugin_name}' manifest not found")

    tools: list[dict[str, Any]] = manifest.get("tools", [])

    # Determine required input type from file MIME type
    required_input = "video" if file_mime.startswith("video/") else "image_bytes"

    # Find all tools matching capability + input type
    candidates = [
        tool["id"]
        for tool in tools
        if logical_tool_id in tool.get("capabilities", [])
        and required_input in tool.get("input_types", [])
    ]

    if not candidates:
        raise ValueError(
            f"No plugin tool found for capability '{logical_tool_id}' "
            f"with input '{required_input}' in plugin '{plugin_name}'. "
            f"Available tools: {[t.get('id') for t in tools]}"
        )

    # Return first matching tool
    return candidates[0]
