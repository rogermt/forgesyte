"""Tests for VisionAnalysisService."""

import base64
import os
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from app.protocols import PluginRegistry, WebSocketProvider
from app.services.vision_analysis import VisionAnalysisService


class TestVisionAnalysisService:
    """Test VisionAnalysisService functionality."""

    @pytest.fixture
    def mock_registry(self):
        return Mock(spec=PluginRegistry)

    @pytest.fixture
    def mock_ws_manager(self):
        ws_manager = Mock(spec=WebSocketProvider)
        ws_manager.send_personal = AsyncMock()
        ws_manager.send_frame_result = AsyncMock()
        return ws_manager

    @pytest.fixture
    def service(self, mock_registry, mock_ws_manager):
        return VisionAnalysisService(plugins=mock_registry, ws_manager=mock_ws_manager)

    @pytest.mark.asyncio
    async def test_handle_frame_success(self, service, mock_registry, mock_ws_manager):
        """Test successful frame handling."""
        mock_plugin = Mock()
        mock_registry.get.return_value = mock_plugin

        frame_data = {
            "data": base64.b64encode(b"image").decode("utf-8"),
            "frame_id": "frame1",
            "options": {},
            "tools": ["tool1"],
        }

        await service.handle_frame("client1", "plugin1", frame_data)

        mock_registry.get.assert_called_with("plugin1")
        mock_ws_manager.send_frame_result.assert_called_once()

        args = mock_ws_manager.send_frame_result.call_args[0]
        assert args[0] == "client1"
        assert args[1] == "frame1"
        assert args[2] == "plugin1"

    @pytest.mark.asyncio
    async def test_handle_frame_plugin_not_found(
        self, service, mock_registry, mock_ws_manager
    ):
        """Test handling when plugin is not found."""
        mock_registry.get.return_value = None

        await service.handle_frame("client1", "unknown_plugin", {})

        mock_ws_manager.send_personal.assert_called_once()
        args = mock_ws_manager.send_personal.call_args[0]
        assert args[0] == "client1"
        assert args[1]["type"] == "error"
        assert "not found" in args[1]["message"]

    @pytest.mark.asyncio
    async def test_handle_frame_with_image_data_field(
        self, service, mock_registry, mock_ws_manager
    ):
        """Test frame handling with 'image_data' field (Issue #21)."""
        mock_plugin = Mock()
        mock_registry.get.return_value = mock_plugin

        # Client sends 'image_data' field, not 'data'
        frame_data = {
            "image_data": base64.b64encode(b"image").decode("utf-8"),
            "frame_id": "frame1",
            "options": {},
            "tools": ["tool1"],
        }

        await service.handle_frame("client1", "plugin1", frame_data)

        # Should succeed with image_data field
        mock_ws_manager.send_frame_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_frame_invalid_data(
        self, service, mock_registry, mock_ws_manager
    ):
        """Test handling invalid frame data (missing both 'data' and 'image_data')."""
        mock_plugin = Mock()
        mock_registry.get.return_value = mock_plugin

        await service.handle_frame("client1", "plugin1", {"frame_id": "frame1"})

        mock_ws_manager.send_personal.assert_called_once()
        args = mock_ws_manager.send_personal.call_args[0]
        assert args[0] == "client1"
        assert args[1]["type"] == "error"
        assert "Invalid frame data" in args[1]["message"]

    @pytest.mark.asyncio
    async def test_handle_frame_missing_tools(
        self, service, mock_registry, mock_ws_manager
    ):
        """Test handling frame data missing 'tools' field (Phase 13 requirement)."""
        mock_plugin = Mock()
        mock_registry.get.return_value = mock_plugin

        frame_data = {
            "data": base64.b64encode(b"image").decode("utf-8"),
            "frame_id": "frame1",
        }

        await service.handle_frame("client1", "plugin1", frame_data)

        mock_ws_manager.send_personal.assert_called_once()
        args = mock_ws_manager.send_personal.call_args[0]
        assert args[0] == "client1"
        assert args[1]["type"] == "error"
        assert "tools" in args[1]["message"]

    @pytest.mark.asyncio
    async def test_handle_frame_analysis_exception(
        self, service, mock_registry, mock_ws_manager
    ):
        """Test handling plugin analysis exception."""
        mock_plugin = Mock()
        mock_registry.get.return_value = mock_plugin

        frame_data = {
            "data": base64.b64encode(b"image").decode("utf-8"),
            "frame_id": "frame1",
            "tools": ["tool1"],
        }

        # Mock video_pipeline_service.run_pipeline to raise exception
        with patch.object(
            service.video_pipeline_service,
            "run_pipeline",
            side_effect=Exception("Analysis Error"),
        ):
            await service.handle_frame("client1", "plugin1", frame_data)

        mock_ws_manager.send_personal.assert_called_once()
        args = mock_ws_manager.send_personal.call_args[0]
        assert args[0] == "client1"
        assert args[1]["type"] == "error"
        assert "Analysis failed" in args[1]["message"]

    @pytest.mark.asyncio
    async def test_list_available_plugins_success(self, service, mock_registry):
        """Test listing available plugins."""
        mock_registry.list.return_value = {"p1": {}, "p2": {}}

        result = await service.list_available_plugins()

        assert len(result) == 2
        assert "p1" in result

    @pytest.mark.asyncio
    async def test_list_available_plugins_exception(self, service, mock_registry):
        """Test exception handling in list_available_plugins."""
        mock_registry.list.side_effect = Exception("Error")

        result = await service.list_available_plugins()

        assert result == {}
