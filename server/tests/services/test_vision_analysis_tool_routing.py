"""TDD tests for tool routing fix in VisionAnalysisService.

Verifies that vision_analysis uses the tool from frame data,
and warns when tool is missing.
"""

import base64
import logging
import os
import sys
from unittest.mock import AsyncMock, Mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from app.protocols import PluginRegistry, WebSocketProvider
from app.services.vision_analysis import VisionAnalysisService


class TestToolRoutingFromFrame:
    """Test that handle_frame uses tool from frame data."""

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
    def service(self, mock_registry, mock_ws_manager):
        return VisionAnalysisService(plugins=mock_registry, ws_manager=mock_ws_manager)

    @pytest.mark.asyncio
    async def test_uses_tool_from_frame_data(
        self, service, mock_registry, mock_ws_manager
    ):
        """When frame includes tool field, run_tool should use that tool."""
        mock_plugin = Mock()
        mock_plugin.run_tool.return_value = {"detections": []}
        mock_registry.get.return_value = mock_plugin

        frame_data = {
            "data": base64.b64encode(b"image").decode("utf-8"),
            "frame_id": "f1",
            "tool": "ball_detection",
            "options": {},
        }

        await service.handle_frame("client1", "plugin1", frame_data)

        mock_plugin.run_tool.assert_called_once()
        call_args = mock_plugin.run_tool.call_args[0]
        assert call_args[0] == "ball_detection"

    @pytest.mark.asyncio
    async def test_warns_when_tool_missing(
        self, service, mock_registry, mock_ws_manager, caplog
    ):
        """When frame omits tool, should log a warning and default."""
        mock_plugin = Mock()
        mock_plugin.run_tool.return_value = {"detections": []}
        mock_registry.get.return_value = mock_plugin

        frame_data = {
            "data": base64.b64encode(b"image").decode("utf-8"),
            "frame_id": "f2",
            "options": {},
        }

        with caplog.at_level(logging.WARNING):
            await service.handle_frame("client1", "plugin1", frame_data)

        assert any(
            "missing" in r.message.lower() and "tool" in r.message.lower()
            for r in caplog.records
        ), f"Expected warning about missing tool, got: {[r.message for r in caplog.records]}"
