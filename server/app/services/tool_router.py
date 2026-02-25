"""Tool resolution service for plugin-agnostic capability matching.

This module handles the resolution of logical tool IDs (from UI) to actual
plugin tool IDs based on file type and tool capabilities.

The backend remains completely plugin-agnostic:
- No hardcoded tool names
- No naming convention assumptions
- No prefix or substring matching on tool IDs
- Plugin manifest is the only source of truth
- Capabilities are the semantic bridge

v0.9.8: Added resolve_tools() for multi-tool resolution.
"""

from typing import Any, Iterable, List

from app.services.plugin_management_service import PluginManagementService


def _iter_manifest_tools(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract tools list from manifest, handling both list and dict formats.

    Args:
        manifest: Plugin manifest dictionary

    Returns:
        List of tool definition dictionaries
    """
    tools = manifest.get("tools", [])
    if isinstance(tools, list):
        return tools
    if isinstance(tools, dict):
        return [{"id": k, **v} for k, v in tools.items()]
    return []


def resolve_tools(
    logical_tool_ids: Iterable[str],
    file_mime: str,
    plugin_name: str,
    plugin_service: PluginManagementService,
) -> List[str]:
    """Resolve multiple logical tool IDs to actual plugin tool IDs.

    Args:
        logical_tool_ids: Iterable of capability strings from UI
        file_mime: MIME type of uploaded file (e.g., "video/mp4", "image/png")
        plugin_name: Name of the plugin to search in
        plugin_service: PluginManagementService instance

    Returns:
        List of actual plugin tool IDs (e.g., ["video_player_tracking", "video_ball_detection"])

    Raises:
        ValueError: If no matching tool found for any logical ID
        ValueError: If plugin_service is None

    Architecture:
        1. Load plugin manifest (source of truth)
        2. Determine required input type from file MIME
        3. For each logical ID:
           - Prefer: logical in tool.capabilities AND required_input in tool.input_types
           - Fallback: tool.id.startswith(logical) AND required_input in tool.input_types
        4. Return list of resolved tool IDs
    """
    if plugin_service is None:
        raise ValueError("plugin_service is required")

    manifest: dict[str, Any] | None = plugin_service.get_plugin_manifest(plugin_name)
    if not manifest:
        raise ValueError(f"Plugin '{plugin_name}' manifest not found")

    tools = _iter_manifest_tools(manifest)

    # Determine required input type from file MIME type
    required_input = (
        "video" if (file_mime or "").startswith("video/") else "image_bytes"
    )

    # Filter tools by input type
    scoped = [t for t in tools if required_input in (t.get("input_types") or [])]

    resolved: list[str] = []
    for logical in logical_tool_ids:
        # Preferred: match by capability
        match = next(
            (t for t in scoped if logical in (t.get("capabilities") or [])), None
        )
        if match:
            resolved.append(match["id"])
            continue

        # Fallback: match by tool ID prefix
        match = next(
            (t for t in scoped if str(t.get("id", "")).startswith(logical)), None
        )
        if match:
            resolved.append(match["id"])
            continue

        raise ValueError(
            f"No plugin tool found for capability '{logical}' "
            f"with input '{required_input}' in plugin '{plugin_name}'. "
            f"Available tools: {[t.get('id') for t in tools]}"
        )

    return resolved


def resolve_tool(
    logical_tool_id: str,
    file_mime: str,
    plugin_name: str,
    plugin_service: PluginManagementService | None = None,
) -> str:
    """Resolve a logical tool ID to an actual plugin tool ID.

    This is a convenience wrapper around resolve_tools() for single-tool resolution.

    Args:
        logical_tool_id: Capability string from UI (e.g., "player_detection")
        file_mime: MIME type of uploaded file (e.g., "video/mp4", "image/png")
        plugin_name: Name of the plugin to search in
        plugin_service: PluginManagementService instance (for dependency injection)

    Returns:
        The actual plugin tool ID (e.g., "video_player_tracking")

    Raises:
        ValueError: If no matching tool found in plugin manifest
    """
    if plugin_service is None:
        raise ValueError("plugin_service is required")
    return resolve_tools([logical_tool_id], file_mime, plugin_name, plugin_service)[0]
