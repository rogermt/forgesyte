"""Tests for capability-based tool resolution.

Tests that the backend can resolve logical tool IDs (from UI)
to actual plugin tool IDs based on file type and capabilities,
without any hardcoding or naming assumptions.

v0.9.8: Added tests for resolve_tools() multi-tool resolution.
"""

from unittest.mock import MagicMock

import pytest

from app.services.plugin_management_service import PluginManagementService
from app.services.tool_router import resolve_tool, resolve_tools


@pytest.fixture
def mock_plugin_service():
    """Mock PluginManagementService with test manifest."""
    service = MagicMock(spec=PluginManagementService)

    def get_manifest_impl(plugin_name: str) -> dict:
        return {
            "name": plugin_name,
            "version": "1.0.0",
            "tools": [
                {
                    "id": "player_detection",
                    "title": "Player Detection (Image)",
                    "input_types": ["image_bytes"],
                    "output_types": ["detections"],
                    "capabilities": ["player_detection"],
                },
                {
                    "id": "video_player_tracking",
                    "title": "Player Tracking (Video)",
                    "input_types": ["video"],
                    "output_types": ["frames"],
                    "capabilities": ["player_detection"],
                },
                {
                    "id": "ball_detection",
                    "title": "Ball Detection (Image)",
                    "input_types": ["image_bytes"],
                    "output_types": ["detections"],
                    "capabilities": ["ball_detection"],
                },
                {
                    "id": "video_ball_detection",
                    "title": "Ball Detection (Video)",
                    "input_types": ["video"],
                    "output_types": ["frames"],
                    "capabilities": ["ball_detection"],
                },
            ],
        }

    service.get_plugin_manifest = get_manifest_impl
    return service


class TestCapabilityResolution:
    """Test capability-based tool resolution."""

    def test_resolve_image_player_detection(self, mock_plugin_service):
        """Verify image file resolves to player_detection tool."""
        tool = resolve_tool(
            "player_detection", "image/png", "test-plugin", mock_plugin_service
        )
        assert tool == "player_detection"

    def test_resolve_video_player_detection(self, mock_plugin_service):
        """Verify video file resolves to video_player_tracking tool."""
        tool = resolve_tool(
            "player_detection", "video/mp4", "test-plugin", mock_plugin_service
        )
        assert tool == "video_player_tracking"

    def test_resolve_image_ball_detection(self, mock_plugin_service):
        """Verify image file resolves to ball_detection tool."""
        tool = resolve_tool(
            "ball_detection", "image/jpeg", "test-plugin", mock_plugin_service
        )
        assert tool == "ball_detection"

    def test_resolve_video_ball_detection(self, mock_plugin_service):
        """Verify video file resolves to video_ball_detection tool."""
        tool = resolve_tool(
            "ball_detection", "video/mp4", "test-plugin", mock_plugin_service
        )
        assert tool == "video_ball_detection"

    def test_missing_capability_raises_error(self, mock_plugin_service):
        """Verify error when capability not found in manifest."""
        with pytest.raises(ValueError) as exc_info:
            resolve_tool(
                "pitch_detection", "image/png", "test-plugin", mock_plugin_service
            )

        assert "No plugin tool found" in str(exc_info.value)
        assert "pitch_detection" in str(exc_info.value)

    def test_missing_input_type_with_unsupported_file(self, mock_plugin_service):
        """Verify error when no tools support the resolved input type."""
        # Try to find a tool with unsupported capability
        with pytest.raises(ValueError) as exc_info:
            resolve_tool(
                "unsupported_capability",
                "image/png",
                "test-plugin",
                mock_plugin_service,
            )

        assert "No plugin tool found" in str(exc_info.value)

    def test_multiple_tools_with_same_capability(self, mock_plugin_service):
        """Verify first matching tool is returned when multiple exist."""
        # Mock has 2 tools for "player_detection" capability
        tool = resolve_tool(
            "player_detection", "image/png", "test-plugin", mock_plugin_service
        )
        assert tool == "player_detection"  # First match

    def test_jpeg_input_type(self, mock_plugin_service):
        """Verify JPEG files are treated as image input."""
        tool = resolve_tool(
            "ball_detection", "image/jpeg", "test-plugin", mock_plugin_service
        )
        assert tool == "ball_detection"

    def test_mov_input_type(self, mock_plugin_service):
        """Verify MOV files are treated as video input."""
        tool = resolve_tool(
            "player_detection", "video/quicktime", "test-plugin", mock_plugin_service
        )
        assert tool == "video_player_tracking"

    def test_avi_input_type(self, mock_plugin_service):
        """Verify AVI files are treated as video input."""
        tool = resolve_tool(
            "ball_detection", "video/x-msvideo", "test-plugin", mock_plugin_service
        )
        assert tool == "video_ball_detection"


class TestMultiToolResolution:
    """Test multi-tool resolution via resolve_tools()."""

    def test_resolve_tools_multiple_logical_ids_video(self, mock_plugin_service):
        """Multiple logical IDs resolve to correct video tools."""
        tools = resolve_tools(
            ["player_detection", "ball_detection"],
            "video/mp4",
            "test-plugin",
            mock_plugin_service,
        )
        assert tools == ["video_player_tracking", "video_ball_detection"]

    def test_resolve_tools_multiple_logical_ids_image(self, mock_plugin_service):
        """Multiple logical IDs resolve to correct image tools."""
        tools = resolve_tools(
            ["player_detection", "ball_detection"],
            "image/png",
            "test-plugin",
            mock_plugin_service,
        )
        assert tools == ["player_detection", "ball_detection"]

    def test_resolve_tools_single_logical_id(self, mock_plugin_service):
        """Single logical ID returns single-element list."""
        tools = resolve_tools(
            ["player_detection"],
            "video/mp4",
            "test-plugin",
            mock_plugin_service,
        )
        assert tools == ["video_player_tracking"]
        assert len(tools) == 1

    def test_resolve_tools_empty_list(self, mock_plugin_service):
        """Empty list returns empty list."""
        tools = resolve_tools(
            [],
            "video/mp4",
            "test-plugin",
            mock_plugin_service,
        )
        assert tools == []

    def test_resolve_tools_partial_match_error(self, mock_plugin_service):
        """Error if one logical ID not found."""
        with pytest.raises(ValueError) as exc_info:
            resolve_tools(
                ["player_detection", "invalid_capability"],
                "video/mp4",
                "test-plugin",
                mock_plugin_service,
            )
        assert "invalid_capability" in str(exc_info.value)

    def test_resolve_tools_preserves_order(self, mock_plugin_service):
        """Resolution preserves the order of input logical IDs."""
        tools = resolve_tools(
            ["ball_detection", "player_detection"],  # reversed order
            "video/mp4",
            "test-plugin",
            mock_plugin_service,
        )
        assert tools == ["video_ball_detection", "video_player_tracking"]

    def test_resolve_tools_missing_plugin_service(self):
        """Error if plugin_service is None."""
        with pytest.raises(ValueError) as exc_info:
            resolve_tools(
                ["player_detection"],
                "video/mp4",
                "test-plugin",
                None,
            )
        assert "plugin_service is required" in str(exc_info.value)

    def test_resolve_tools_plugin_not_found(self, mock_plugin_service):
        """Error if plugin manifest not found."""
        # Override to return None for this test
        mock_plugin_service.get_plugin_manifest = lambda name: None
        with pytest.raises(ValueError) as exc_info:
            resolve_tools(
                ["player_detection"],
                "video/mp4",
                "nonexistent-plugin",
                mock_plugin_service,
            )
        assert "manifest not found" in str(exc_info.value)


class TestManifestToolsIteration:
    """Test _iter_manifest_tools helper handles both list and dict formats."""

    def test_tools_as_list(self, mock_plugin_service):
        """Manifest with tools as list works correctly."""
        tools = resolve_tools(
            ["player_detection"],
            "image/png",
            "test-plugin",
            mock_plugin_service,
        )
        assert tools == ["player_detection"]

    def test_tools_as_dict(self):
        """Manifest with tools as dict format works correctly."""
        service = MagicMock(spec=PluginManagementService)
        service.get_plugin_manifest = lambda name: {
            "name": name,
            "version": "1.0.0",
            "tools": {
                "player_detection": {
                    "title": "Player Detection",
                    "input_types": ["image_bytes"],
                    "capabilities": ["player_detection"],
                },
                "video_player_tracking": {
                    "title": "Player Tracking",
                    "input_types": ["video"],
                    "capabilities": ["player_detection"],
                },
            },
        }

        tools = resolve_tools(
            ["player_detection"],
            "video/mp4",
            "test-plugin",
            service,
        )
        assert tools == ["video_player_tracking"]
