"""Pytest configuration for server tests."""

import os
import sys

import pytest

# Set asyncio mode before pytest-asyncio imports
pytest_plugins = ("pytest_asyncio",)

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set asyncio event loop policy."""
    import asyncio

    return asyncio.get_event_loop_policy()


def pytest_configure(config):
    """Register custom markers and configure asyncio."""
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.option.asyncio_mode = "auto"


@pytest.fixture
def app_with_plugins():
    """Create app with plugins and services initialized."""
    from app.auth import init_auth_service
    from app.main import app
    from app.plugin_loader import PluginManager
    from app.services import (
        AnalysisService,
        ImageAcquisitionService,
        JobManagementService,
        PluginManagementService,
        VisionAnalysisService,
    )
    from app.tasks import init_task_processor
    from app.websocket_manager import ws_manager

    # Initialize authentication service
    init_auth_service()

    # Load plugins
    plugins_dir = os.getenv("FORGESYTE_PLUGINS_DIR", "../example_plugins")
    plugin_manager = PluginManager(plugins_dir)
    plugin_manager.load_plugins()
    app.state.plugins = plugin_manager

    # Initialize task processor
    init_task_processor(plugin_manager)

    # Initialize services
    from app import tasks as tasks_module

    # Vision analysis service for WebSocket
    app.state.analysis_service = VisionAnalysisService(plugin_manager, ws_manager)

    # REST API services - get fresh references from modules
    image_acquisition = ImageAcquisitionService()
    app.state.analysis_service_rest = AnalysisService(
        tasks_module.task_processor, image_acquisition
    )
    app.state.job_service = JobManagementService(
        tasks_module.job_store, tasks_module.task_processor
    )
    app.state.plugin_service = PluginManagementService(plugin_manager)

    return app
