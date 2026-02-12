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
    def service(self, mock_registry, mock_ws_manager):
        return VisionAnalysisService(plugins=mock_registry, ws_manager=mock_ws_manager)

    @pytest.mark.asyncio
    async def test_uses_tools_from_frame_data(
        self, service, mock_registry, mock_ws_manager
    ):
        """When frame includes tools field, run_pipeline should use those tools."""
        mock_plugin = Mock()
        mock_registry.get.return_value = mock_plugin

        frame_data = {
            "data": base64.b64encode(b"image").decode("utf-8"),
            "frame_id": "f1",
            "tools": ["ball_detection", "player_detection"],
            "options": {},
        }

        with patch.object(
            service.video_pipeline_service,
            "run_pipeline",
            return_value={"detections": []},
        ) as mock_run_pipeline:
            await service.handle_frame("client1", "plugin1", frame_data)

        mock_run_pipeline.assert_called_once()
        call_kwargs = mock_run_pipeline.call_args[1]
        assert call_kwargs["tools"] == ["ball_detection", "player_detection"]
        assert call_kwargs["plugin_id"] == "plugin1"

    @pytest.mark.asyncio
    async def test_errors_when_tools_missing(
        self, service, mock_registry, mock_ws_manager
    ):
        """When frame omits tools, should return an error (Phase 13 requirement)."""
        mock_plugin = Mock()
        mock_registry.get.return_value = mock_plugin

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
