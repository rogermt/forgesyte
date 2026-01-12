"""Pytest configuration for server tests.

This module provides pytest fixtures for testing ForgeSyte components with
Protocol-based mocks. The fixtures enable easy testing of services without
heavy dependencies or external resources.

Fixtures:
    - event_loop_policy: Asyncio event loop configuration
    - app_with_plugins: FastAPI app with real plugins (integration tests)
    - mock_plugin_registry: Mock PluginRegistry for unit tests
    - mock_job_store: Mock JobStore for task tests
    - mock_task_processor: Mock TaskProcessor for service tests
"""

import os
import sys
from typing import Any, Dict, Optional

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
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.option.asyncio_mode = "auto"


@pytest.fixture
def app_with_plugins():
    """Create app with plugins and services initialized.

    This is an integration test fixture that loads real plugins from the
    file system. Use mock_plugin_registry for unit tests.

    Returns:
        FastAPI app with all services initialized and plugins loaded
    """
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


@pytest.fixture
async def client(app_with_plugins):
    """Create AsyncClient for testing API endpoints.

    This fixture is used for integration tests that need to make actual
    HTTP requests to the FastAPI application.

    Returns:
        AsyncClient configured with the app_with_plugins app
    """
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app_with_plugins)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


# Protocol-based mock fixtures for unit tests
class MockPluginRegistry:
    """Mock PluginRegistry implementing the PluginRegistry Protocol.

    Provides in-memory plugin storage for testing without file system
    dependencies. Satisfies the PluginRegistry Protocol interface.
    """

    def __init__(self) -> None:
        """Initialize with empty plugin registry."""
        self._plugins: Dict[str, Any] = {}
        self._plugin_instances: Dict[str, Any] = {}

    def get(self, name: str) -> Optional[Any]:
        """Retrieve a loaded plugin by name.

        Args:
            name: Plugin identifier

        Returns:
            Plugin instance if found, None otherwise
        """
        return self._plugin_instances.get(name)

    def list(self) -> Dict[str, Dict[str, Any]]:
        """Get all loaded plugins with their metadata.

        Returns:
            Dictionary mapping plugin names to their metadata dictionaries
        """
        return dict(self._plugins)

    def reload_plugin(self, name: str) -> bool:
        """Reload a specific plugin (no-op in mock).

        Args:
            name: Plugin identifier

        Returns:
            True if plugin exists, False otherwise
        """
        return name in self._plugins

    def reload_all(self) -> Dict[str, Any]:
        """Reload all plugins (no-op in mock).

        Returns:
            Dictionary of reload results
        """
        return {name: {"status": "success"} for name in self._plugins}

    def add_plugin(
        self, name: str, metadata: Dict[str, Any], instance: Any = None
    ) -> None:
        """Add a mock plugin for testing.

        Args:
            name: Plugin name
            metadata: Plugin metadata
            instance: Plugin instance (optional)
        """
        self._plugins[name] = metadata
        if instance is not None:
            self._plugin_instances[name] = instance


@pytest.fixture
def mock_plugin_registry() -> MockPluginRegistry:
    """Provide a mock PluginRegistry for unit tests.

    Returns:
        MockPluginRegistry instance with Protocol-compatible interface
    """
    return MockPluginRegistry()


class MockJobStore:
    """Mock JobStore implementing the JobStore Protocol.

    Provides in-memory job storage for testing without database dependencies.
    Satisfies the JobStore Protocol interface.
    """

    def __init__(self) -> None:
        """Initialize with empty job store."""
        self._jobs: Dict[str, Dict[str, Any]] = {}

    async def create(self, plugin_name: str, request_data: Dict[str, Any]) -> str:
        """Create a new job.

        Args:
            plugin_name: Name of plugin to run
            request_data: Request data (image URL, options, etc.)

        Returns:
            Job ID
        """
        import uuid

        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "job_id": job_id,
            "plugin": plugin_name,
            "status": "pending",
            "request_data": request_data,
        }
        return job_id

    async def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a job by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job data if found, None otherwise
        """
        return self._jobs.get(job_id)

    async def list_jobs(self, limit: int = 100) -> list:
        """List all jobs up to limit.

        Args:
            limit: Maximum number of jobs to return

        Returns:
            List of job records
        """
        return list(self._jobs.values())[:limit]

    async def update(self, job_id: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """Update a job.

        Args:
            job_id: Job identifier
            **kwargs: Fields to update

        Returns:
            Updated job data if found, None otherwise
        """
        if job_id not in self._jobs:
            return None
        self._jobs[job_id].update(kwargs)
        return self._jobs[job_id]

    async def delete(self, job_id: str) -> bool:
        """Delete a job.

        Args:
            job_id: Job identifier

        Returns:
            True if deleted, False if not found
        """
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False


@pytest.fixture
def mock_job_store() -> MockJobStore:
    """Provide a mock JobStore for unit tests.

    Returns:
        MockJobStore instance with Protocol-compatible interface
    """
    return MockJobStore()


class MockTaskProcessor:
    """Mock TaskProcessor implementing the TaskProcessor Protocol.

    Provides in-memory task processing for testing without async overhead.
    Satisfies the TaskProcessor Protocol interface.
    """

    def __init__(self, job_store: Optional[MockJobStore] = None) -> None:
        """Initialize task processor.

        Args:
            job_store: Optional JobStore instance
        """
        self.job_store = job_store or MockJobStore()
        self._results: Dict[str, Any] = {}

    async def process_job(
        self, job_id: str, plugin_name: str, analysis_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a job (no-op in mock).

        Args:
            job_id: Job identifier
            plugin_name: Plugin to use
            analysis_data: Analysis parameters

        Returns:
            Processing result
        """
        return {
            "job_id": job_id,
            "status": "completed",
            "result": "mock_result",
        }

    async def get_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job result.

        Args:
            job_id: Job identifier

        Returns:
            Result if available, None otherwise
        """
        return self._results.get(job_id)

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job (no-op in mock).

        Args:
            job_id: Job identifier

        Returns:
            True if cancelled, False if not found or already complete
        """
        return True

    def add_on_complete_callback(self, callback: Any) -> None:
        """Add completion callback (no-op in mock).

        Args:
            callback: Async callback function
        """
        pass

    def remove_callback(self, callback: Any) -> None:
        """Remove completion callback (no-op in mock).

        Args:
            callback: Callback to remove
        """
        pass


@pytest.fixture
def mock_task_processor(mock_job_store: MockJobStore) -> MockTaskProcessor:
    """Provide a mock TaskProcessor for unit tests.

    Args:
        mock_job_store: Fixture providing MockJobStore

    Returns:
        MockTaskProcessor instance with Protocol-compatible interface
    """
    return MockTaskProcessor(mock_job_store)
