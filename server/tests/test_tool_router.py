"""Tests for capability-based tool resolution.

Tests that the backend can resolve logical tool IDs (from UI)
to actual plugin tool IDs based on file type and capabilities,
without any hardcoding or naming assumptions.
"""

from unittest.mock import MagicMock

import pytest

from app.services.plugin_management_service import PluginManagementService
from app.services.tool_router import resolve_tool


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
