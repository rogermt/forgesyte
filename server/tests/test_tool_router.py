"""Tests for tool_router service - capability-based resolution.

These tests verify the plugin-agnostic tool resolution that maps logical tool IDs
to actual plugin tool IDs using CAPABILITY matching (not substring or prefix).

Architecture verified:
- NO hardcoded tool names in backend
- NO substring or prefix matching
- Plugin manifest is the ONLY source of truth
- Capabilities are the semantic bridge between UI and plugin tools
"""

import pytest

from app.services.tool_router import resolve_tool


@pytest.fixture
def mock_manifest(monkeypatch):
    """Mock plugin manifest with capabilities for testing.

    This simulates a plugin that provides both image and video tools
    for the same logical capabilities (player_detection, ball_detection).
    """

    def fake_get_manifest(plugin_name: str):
        return {
            "name": plugin_name,
            "version": "1.0.0",
            "tools": [
                {
                    "id": "player_detection",
                    "title": "Player Detection (Image)",
                    "input_types": ["image_bytes"],
                    "output_types": ["detections", "annotated_image_base64"],
                    "capabilities": ["player_detection"],
                },
                {
                    "id": "video_player_tracking",
                    "title": "Player Tracking (Video)",
                    "input_types": ["video"],
                    "output_types": ["frames", "total_frames"],
                    "capabilities": ["player_detection"],
                },
                {
                    "id": "ball_detection",
                    "title": "Ball Detection (Image)",
                    "input_types": ["image_bytes"],
                    "output_types": ["detections", "annotated_image_base64"],
                    "capabilities": ["ball_detection"],
                },
                {
                    "id": "video_ball_detection",
                    "title": "Ball Detection (Video)",
                    "input_types": ["video"],
                    "output_types": ["frames", "total_frames"],
                    "capabilities": ["ball_detection"],
                },
                {
                    "id": "pitch_detection",
                    "title": "Pitch Detection (Image)",
                    "input_types": ["image_bytes"],
                    "output_types": ["detections"],
                    "capabilities": ["pitch_detection"],
                },
                {
                    "id": "video_pitch_detection",
                    "title": "Pitch Detection (Video)",
                    "input_types": ["video"],
                    "output_types": ["frames"],
                    "capabilities": ["pitch_detection"],
                },
                {
                    "id": "radar",
                    "title": "Radar View (Image)",
                    "input_types": ["image_bytes"],
                    "output_types": ["radar_data"],
                    "capabilities": ["radar"],
                },
                {
                    "id": "video_radar",
                    "title": "Radar View (Video)",
                    "input_types": ["video"],
                    "output_types": ["radar_frames"],
                    "capabilities": ["radar"],
                },
            ],
        }

    monkeypatch.setattr(
        "app.services.tool_router.get_plugin_manifest",
        fake_get_manifest,
    )


class TestResolveToolCapabilityMatch:
    """Test capability-based tool resolution for all 4 logical tools."""

    def test_resolve_image_player_detection(self, mock_manifest):
        """Image file with player_detection capability -> image tool."""
        tool = resolve_tool("player_detection", "image/png", "test-plugin")
        assert tool == "player_detection"

    def test_resolve_video_player_detection(self, mock_manifest):
        """Video file with player_detection capability -> video tool.

        Key test: logical ID 'player_detection' != tool ID 'video_player_tracking'
        This verifies capability matching (not substring) works correctly.
        """
        tool = resolve_tool("player_detection", "video/mp4", "test-plugin")
        assert tool == "video_player_tracking"

    def test_resolve_image_ball_detection(self, mock_manifest):
        """Image file with ball_detection capability -> image tool."""
        tool = resolve_tool("ball_detection", "image/jpeg", "test-plugin")
        assert tool == "ball_detection"

    def test_resolve_video_ball_detection(self, mock_manifest):
        """Video file with ball_detection capability -> video tool."""
        tool = resolve_tool("ball_detection", "video/mp4", "test-plugin")
        assert tool == "video_ball_detection"

    def test_resolve_image_pitch_detection(self, mock_manifest):
        """Image file with pitch_detection capability -> image tool."""
        tool = resolve_tool("pitch_detection", "image/png", "test-plugin")
        assert tool == "pitch_detection"

    def test_resolve_video_pitch_detection(self, mock_manifest):
        """Video file with pitch_detection capability -> video tool."""
        tool = resolve_tool("pitch_detection", "video/mp4", "test-plugin")
        assert tool == "video_pitch_detection"

    def test_resolve_image_radar(self, mock_manifest):
        """Image file with radar capability -> image tool."""
        tool = resolve_tool("radar", "image/png", "test-plugin")
        assert tool == "radar"

    def test_resolve_video_radar(self, mock_manifest):
        """Video file with radar capability -> video tool."""
        tool = resolve_tool("radar", "video/mp4", "test-plugin")
        assert tool == "video_radar"


class TestResolveToolMimeTypeVariants:
    """Test various MIME type formats."""

    def test_image_jpeg(self, mock_manifest):
        """JPEG image MIME type."""
        tool = resolve_tool("player_detection", "image/jpeg", "test-plugin")
        assert tool == "player_detection"

    def test_image_png(self, mock_manifest):
        """PNG image MIME type."""
        tool = resolve_tool("player_detection", "image/png", "test-plugin")
        assert tool == "player_detection"

    def test_image_webp(self, mock_manifest):
        """WebP image MIME type."""
        tool = resolve_tool("player_detection", "image/webp", "test-plugin")
        assert tool == "player_detection"

    def test_video_mp4(self, mock_manifest):
        """MP4 video MIME type."""
        tool = resolve_tool("player_detection", "video/mp4", "test-plugin")
        assert tool == "video_player_tracking"

    def test_video_quicktime(self, mock_manifest):
        """QuickTime video MIME type."""
        tool = resolve_tool("player_detection", "video/quicktime", "test-plugin")
        assert tool == "video_player_tracking"

    def test_video_webm(self, mock_manifest):
        """WebM video MIME type."""
        tool = resolve_tool("player_detection", "video/webm", "test-plugin")
        assert tool == "video_player_tracking"


class TestResolveToolErrors:
    """Test error handling for tool resolution."""

    def test_missing_capability_raises_error(self, mock_manifest):
        """Missing capability should raise ValueError with clear message."""
        with pytest.raises(ValueError) as exc_info:
            resolve_tool("nonexistent_capability", "image/png", "test-plugin")

        assert "No plugin tool found for capability 'nonexistent_capability'" in str(
            exc_info.value
        )

    def test_unsupported_file_type_raises_error(self, mock_manifest):
        """Unsupported MIME type should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            resolve_tool("player_detection", "audio/mp3", "test-plugin")

        assert "Unsupported file type: audio/mp3" in str(exc_info.value)

    def test_plugin_not_found_raises_error(self, monkeypatch):
        """Missing plugin should raise ValueError from get_plugin_manifest."""
        from app.services import tool_router

        def raise_not_found(plugin_name: str):
            raise ValueError(f"Plugin '{plugin_name}' not found or has no manifest")

        monkeypatch.setattr(tool_router, "get_plugin_manifest", raise_not_found)

        with pytest.raises(ValueError) as exc_info:
            resolve_tool("player_detection", "image/png", "missing-plugin")

        assert "not found" in str(exc_info.value)


class TestResolveToolPluginAgnostic:
    """Test that resolution works with ANY plugin naming scheme."""

    @pytest.fixture
    def weird_naming_manifest(self, monkeypatch):
        """Plugin with unusual tool naming - proves no substring assumptions."""

        def fake_get_manifest(plugin_name: str):
            return {
                "name": plugin_name,
                "tools": [
                    {
                        "id": "detect_players_v2_image",  # Weird name
                        "input_types": ["image_bytes"],
                        "capabilities": ["player_detection"],  # Standard capability
                    },
                    {
                        "id": "track_players_on_field_video",  # Different weird name
                        "input_types": ["video"],
                        "capabilities": ["player_detection"],  # Same capability
                    },
                ],
            }

        monkeypatch.setattr(
            "app.services.tool_router.get_plugin_manifest",
            fake_get_manifest,
        )

    def test_weird_naming_image(self, weird_naming_manifest):
        """Resolution works regardless of tool naming scheme."""
        tool = resolve_tool("player_detection", "image/png", "weird-plugin")
        assert tool == "detect_players_v2_image"

    def test_weird_naming_video(self, weird_naming_manifest):
        """Resolution works regardless of tool naming scheme."""
        tool = resolve_tool("player_detection", "video/mp4", "weird-plugin")
        assert tool == "track_players_on_field_video"
