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
    """Create app with plugins initialized."""
    from app.auth import init_api_keys
    from app.main import app
    from app.plugin_loader import PluginManager
    from app.tasks import init_task_processor

    # Initialize API keys
    init_api_keys()

    # Load plugins
    plugins_dir = os.getenv("FORGESYTE_PLUGINS_DIR", "../example_plugins")
    plugin_manager = PluginManager(plugins_dir)
    plugin_manager.load_plugins()
    app.state.plugins = plugin_manager

    # Initialize task processor
    init_task_processor(plugin_manager)

    return app
