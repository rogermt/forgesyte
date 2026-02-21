"""TDD tests for tool routing fix in VisionAnalysisService.

Verifies that vision_analysis uses the tools from frame data,
and errors when tools is missing (Phase 13 multi-tool requirement).
"""

import base64
import os
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from app.protocols import PluginRegistry, WebSocketProvider
from app.services.plugin_management_service import PluginManagementService
from app.services.vision_analysis import VisionAnalysisService


class TestToolRoutingFromFrame:
    """Test that handle_frame uses tools from frame data."""

    @pytest.fixture
    def mock_registry(self):
        return Mock(spec=PluginRegistry)

    @pytest.fixture
    def mock_ws_manager(self):
        ws = Mock(spec=WebSocketProvider)
        ws.send_personal = AsyncMock()
        ws.send_frame_result = AsyncMock()
        return ws

    @pytest.fixture
    def plugin_service(self, mock_registry):
        return Mock(spec=PluginManagementService)

    @pytest.fixture
    def service(self, plugin_service, mock_ws_manager):
        return VisionAnalysisService(
            plugin_service=plugin_service, ws_manager=mock_ws_manager
        )

    @pytest.mark.asyncio
    async def test_uses_tools_from_frame_data(
        self, service, plugin_service, mock_ws_manager
    ):
        """When frame includes tools field, run_plugin_tool should use those tools."""
        plugin_service.run_plugin_tool.return_value = {"detections": []}

        frame_data = {
            "data": base64.b64encode(b"image").decode("utf-8"),
            "frame_id": "f1",
            "tools": ["ball_detection", "player_detection"],
            "options": {},
        }

        await service.handle_frame("client1", "plugin1", frame_data)

        # Should call run_plugin_tool for each tool
        assert plugin_service.run_plugin_tool.call_count == 2

        # First call should be for ball_detection
        first_call = plugin_service.run_plugin_tool.call_args_list[0]
        assert first_call[1]["tool_name"] == "ball_detection"
        assert first_call[1]["plugin_id"] == "plugin1"

        # Second call should be for player_detection
        second_call = plugin_service.run_plugin_tool.call_args_list[1]
        assert second_call[1]["tool_name"] == "player_detection"
        assert second_call[1]["plugin_id"] == "plugin1"

    @pytest.mark.asyncio
    async def test_errors_when_tools_missing(
        self, service, mock_ws_manager
    ):
        """When frame omits tools, should return an error (Phase 13 requirement)."""
        frame_data = {
            "data": base64.b64encode(b"image").decode("utf-8"),
            "frame_id": "f2",
            "options": {},
        }

        await service.handle_frame("client1", "plugin1", frame_data)

        mock_ws_manager.send_personal.assert_called_once()
        args = mock_ws_manager.send_personal.call_args[0]
        assert args[0] == "client1"
        assert args[1]["type"] == "error"
        assert "tools" in args[1]["message"]