"""Tests for HealthCheckService."""

import os
import sys
from unittest.mock import Mock

import pytest

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from app.protocols import PluginRegistry, TaskProcessor, WebSocketProvider
from app.services.health_check import HealthCheckService


class TestHealthCheckService:
    """Test HealthCheckService functionality."""

    @pytest.fixture
    def mock_plugins(self):
        plugins = Mock(spec=PluginRegistry)
        plugins.list.return_value = {"plugin1": {"version": "1.0.0"}}
        return plugins

    @pytest.fixture
    def mock_task_processor(self):
        return Mock(spec=TaskProcessor)

    @pytest.fixture
    def mock_ws_manager(self):
        return Mock(spec=WebSocketProvider)

    @pytest.fixture
    def service(self, mock_plugins, mock_task_processor, mock_ws_manager):
        return HealthCheckService(
            plugins=mock_plugins,
            task_processor=mock_task_processor,
            ws_manager=mock_ws_manager,
        )

    def test_init_validates_version(self):
        """Test initialization validates version."""
        with pytest.raises(ValueError):
            HealthCheckService(version="")

    @pytest.mark.asyncio
    async def test_get_health_status_healthy(self, service):
        """Test healthy status when all components are available."""
        status = await service.get_health_status()

        assert status["status"] == "healthy"
        assert status["version"] == "0.1.0"
        assert status["components"]["plugins"]["status"] == "healthy"
        assert status["components"]["task_processor"]["status"] == "healthy"
        assert status["components"]["websocket"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_health_status_no_components(self):
        """Test status when no components are provided."""
        service = HealthCheckService()
        status = await service.get_health_status()

        assert status["status"] == "unknown"
        assert status["components"]["plugins"]["status"] == "unknown"

    @pytest.mark.asyncio
    async def test_get_health_status_plugin_failure(self, service, mock_plugins):
        """Test status when plugin check fails."""
        mock_plugins.list.side_effect = Exception("Plugin error")

        status = await service.get_health_status()

        assert status["status"] == "unhealthy"
        assert status["components"]["plugins"]["status"] == "unhealthy"
        assert "Plugin error" in status["components"]["plugins"]["error"]

    @pytest.mark.asyncio
    async def test_get_plugin_health(self, service):
        """Test detailed plugin health."""
        health = await service.get_plugin_health()

        assert health["status"] == "healthy"
        assert "plugin1" in health["plugins"]
        assert health["plugins"]["plugin1"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_plugin_health_no_plugins(self):
        """Test plugin health when plugins service is missing."""
        service = HealthCheckService()
        health = await service.get_plugin_health()

        assert health["status"] == "unknown"

    @pytest.mark.asyncio
    async def test_get_plugin_health_exception(self, service, mock_plugins):
        """Test plugin health handles exceptions."""
        mock_plugins.list.side_effect = Exception("Registry error")

        health = await service.get_plugin_health()

        assert health["status"] == "unhealthy"
        assert "Registry error" in health["error"]
