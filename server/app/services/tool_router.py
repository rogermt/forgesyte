"""Tool router service for dynamic plugin tool resolution.

This module provides plugin-agnostic tool resolution that maps logical tool IDs
from the UI to actual plugin tool IDs using CAPABILITY matching.

Architecture Principles:
- NO hardcoded tool names in backend
- NO substring or prefix matching
- Plugin manifest is the ONLY source of truth
- Capabilities are the semantic bridge between UI logical tools and plugin tools
- Works for ANY plugin, ANY sport, ANY naming scheme

Resolution Flow:
    UI logical_tool_id → capability match → input_type filter → plugin tool ID

Example:
    >>> from app.services.tool_router import resolve_tool
    >>> # UI sends logical tool "player_detection" for a video file
    >>> tool_id = resolve_tool("player_detection", "video/mp4", "my-plugin")
    >>> print(tool_id)
    "video_player_tracking"  # Found via capabilities: ["player_detection"]

Why Capabilities:
    - UI logical tool ID == capability string
    - Both image and video tools can share the same capability
    - Plugin defines capabilities, backend stays generic
    - No naming assumptions, no coupling

See: GitHub Discussion #223 - v0.9.7 Hotfix Take 2
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def get_plugin_manifest(plugin_name: str) -> Dict[str, Any]:
    """Get plugin manifest from loaded plugins.

    This is a thin wrapper around PluginManagementService.get_plugin_manifest()
    to allow easy mocking in tests.

    Args:
        plugin_name: Plugin identifier

    Returns:
        Plugin manifest dict with 'tools' array

    Raises:
        ValueError: If plugin not found or manifest unavailable
    """
    from app.plugin_loader import PluginRegistry
    from app.services.plugin_management_service import PluginManagementService

    registry = PluginRegistry()
    registry.load_plugins()

    service = PluginManagementService(registry)
    manifest = service.get_plugin_manifest(plugin_name)

    if manifest is None:
        raise ValueError(f"Plugin '{plugin_name}' not found or has no manifest")

    return manifest


def resolve_tool(logical_tool_id: str, file_mime: str, plugin_name: str) -> str:
    """Dynamically resolve a plugin tool ID based on capability and file type.

    This function implements CAPABILITY matching (not substring or prefix) to find
    the appropriate plugin tool. The logical tool ID is matched against the
    tool's capabilities array.

    Args:
        logical_tool_id: Logical tool string from UI (matches capability string)
        file_mime: MIME type of uploaded file (e.g., "image/png", "video/mp4")
        plugin_name: Plugin identifier

    Returns:
        The resolved plugin tool ID

    Raises:
        ValueError: If no matching tool found

    Examples:
        >>> # Image file -> image tool with matching capability
        >>> resolve_tool("player_detection", "image/png", "my-plugin")
        "player_detection"

        >>> # Video file -> video tool with matching capability
        >>> resolve_tool("player_detection", "video/mp4", "my-plugin")
        "video_player_tracking"  # Found via capabilities: ["player_detection"]

        >>> # Ball detection for video
        >>> resolve_tool("ball_detection", "video/mp4", "my-plugin")
        "video_ball_detection"
    """
    manifest = get_plugin_manifest(plugin_name)
    tools = manifest.get("tools", [])

    # Determine required input type based on file MIME
    if file_mime.startswith("video/"):
        required_input = "video"
    elif file_mime.startswith("image/"):
        required_input = "image_bytes"
    else:
        raise ValueError(
            f"Unsupported file type: {file_mime}. " f"Expected image/* or video/*"
        )

    # CAPABILITY match: logical tool ID must be in tool's capabilities array
    # This is the semantic bridge between UI logical tools and plugin tools
    candidates: List[str] = [
        tool["id"]
        for tool in tools
        if logical_tool_id in tool.get("capabilities", [])
        and required_input in tool.get("input_types", [])
    ]

    if not candidates:
        raise ValueError(
            f"No plugin tool found for capability '{logical_tool_id}' "
            f"with input '{required_input}' in plugin '{plugin_name}'"
        )

    # Return first match (list order from manifest)
    result = candidates[0]
    logger.debug(
        f"Resolved tool: capability='{logical_tool_id}' -> plugin_tool='{result}' "
        f"(input={required_input}, plugin={plugin_name})"
    )

    return result
