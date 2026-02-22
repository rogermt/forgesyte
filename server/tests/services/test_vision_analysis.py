"""Tests for VisionAnalysisService."""

import base64
import os
import sys
from unittest.mock import AsyncMock, Mock

import pytest

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from app.protocols import PluginRegistry, WebSocketProvider
from app.services.plugin_management_service import PluginManagementService
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
    def plugin_service(self, mock_registry):
        service = Mock(spec=PluginManagementService)
        service.list_plugins = AsyncMock()
        service.run_plugin_tool = Mock()
        return service

    @pytest.fixture
    def service(self, plugin_service, mock_ws_manager):
        return VisionAnalysisService(
            plugin_service=plugin_service, ws_manager=mock_ws_manager
        )

    @pytest.mark.asyncio
    async def test_handle_frame_success(self, service, plugin_service, mock_ws_manager):
        """Test successful frame handling."""
        plugin_service.run_plugin_tool.return_value = {"objects": []}

        frame_data = {
            "data": base64.b64encode(b"image").decode("utf-8"),
            "frame_id": "frame1",
            "options": {},
            "tools": ["tool1"],
        }

        await service.handle_frame("client1", "plugin1", frame_data)

        plugin_service.run_plugin_tool.assert_called_once()
        mock_ws_manager.send_frame_result.assert_called_once()

        args = mock_ws_manager.send_frame_result.call_args[0]
        assert args[0] == "client1"
        assert args[1] == "frame1"
        assert args[2] == "plugin1"
        # Should receive the final output
        assert args[3] == {"objects": []}

    @pytest.mark.asyncio
    async def test_handle_frame_plugin_not_found(
        self, service, plugin_service, mock_ws_manager
    ):
        """Test handling when plugin is not found."""
        plugin_service.run_plugin_tool.side_effect = ValueError(
            "Plugin 'unknown_plugin' not found"
        )

        frame_data = {
            "data": base64.b64encode(b"image").decode("utf-8"),
            "frame_id": "frame1",
            "tools": ["tool1"],
        }

        await service.handle_frame("client1", "unknown_plugin", frame_data)

        mock_ws_manager.send_personal.assert_called_once()
        args = mock_ws_manager.send_personal.call_args[0]
        assert args[0] == "client1"
        assert args[1]["type"] == "error"
        assert "not found" in args[1]["message"]

    @pytest.mark.asyncio
    async def test_handle_frame_with_image_data_field(
        self, service, plugin_service, mock_ws_manager
    ):
        """Test frame handling with 'image_data' field (Issue #21)."""
        plugin_service.run_plugin_tool.return_value = {"objects": []}

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
    async def test_handle_frame_invalid_data(self, service, mock_ws_manager):
        """Test handling invalid frame data (missing both 'data' and 'image_data')."""
        await service.handle_frame("client1", "plugin1", {"frame_id": "frame1"})

        mock_ws_manager.send_personal.assert_called_once()
        args = mock_ws_manager.send_personal.call_args[0]
        assert args[0] == "client1"
        assert args[1]["type"] == "error"
        assert "Invalid frame data" in args[1]["message"]

    @pytest.mark.asyncio
    async def test_handle_frame_missing_tools(self, service, mock_ws_manager):
        """Test handling frame data missing 'tools' field (Phase 13 requirement)."""
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
        self, service, plugin_service, mock_ws_manager
    ):
        """Test handling plugin analysis exception."""
        plugin_service.run_plugin_tool.side_effect = Exception("Analysis Error")

        frame_data = {
            "data": base64.b64encode(b"image").decode("utf-8"),
            "frame_id": "frame1",
            "tools": ["tool1"],
        }

        await service.handle_frame("client1", "plugin1", frame_data)

        mock_ws_manager.send_personal.assert_called_once()
        args = mock_ws_manager.send_personal.call_args[0]
        assert args[0] == "client1"
        assert args[1]["type"] == "error"
        assert "Analysis failed" in args[1]["message"]

    @pytest.mark.asyncio
    async def test_list_available_plugins_success(self, service, plugin_service):
        """Test listing available plugins."""
        plugin_service.list_plugins.return_value = [{"name": "p1"}, {"name": "p2"}]

        result = await service.list_available_plugins()

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_available_plugins_exception(self, service, plugin_service):
        """Test exception handling in list_available_plugins."""
        plugin_service.list_plugins.side_effect = Exception("Error")

        result = await service.list_available_plugins()

        # Should return empty list on exception (not empty dict)
        assert result == []
