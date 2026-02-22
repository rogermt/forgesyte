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

API Contract Guarantees:
    Tests with API contract guarantees (verified by integration tests in
    server/tests/integration/test_api_contracts.py):

    ✅ GET /v1/jobs - Returns JobResponse list with fields: job_id, status, plugin,
       created_at, completed_at (opt), result (opt), error (opt), progress (opt)
       Reference: tests/integration/test_api_contracts.py:TestJobsEndpointContract

    ✅ GET /v1/jobs/{id} - Returns single JobResponse with same schema
       Reference: tests/integration/test_api_contracts.py:TestSingleJobEndpointContract

    ✅ GET /v1/plugins - Returns PluginMetadata list with fields: name, description,
       version, inputs, outputs, permissions (opt), config_schema (opt)
       Reference: tests/integration/test_api_contracts.py:TestPluginsEndpointContract

    ✅ GET /v1/health - Returns health with status, version, plugins_loaded
       Reference: tests/integration/test_api_contracts.py:TestFixtureConsistency

    Golden Fixtures Reference:
    - fixtures/api-responses.json contains real API response examples
    - All unit test mocks should match fixture field names and structure
    - Integration tests verify real API responses match fixtures
"""

import os
import sys
from typing import Any, Dict, Optional

# ============================================================================
# SET ENV VARS BEFORE ANY APP IMPORTS (CRITICAL)
# ============================================================================

# Disable job worker thread in pytest (prevents DuckDB file lock errors)
os.environ["FORGESYTE_ENABLE_WORKERS"] = "0"

# Use in-memory DuckDB for tests (isolated, fast, no lock contention)
os.environ["FORGESYTE_DATABASE_URL"] = "duckdb:///:memory:"

# Configure authentication BEFORE importing app or pytest
# This ensures that when app.main initializes during TestClient creation,
# it will have API keys configured and enforce authentication
os.environ.setdefault("FORGESYTE_ADMIN_KEY", "test-admin-key")
os.environ.setdefault("FORGESYTE_USER_KEY", "test-user-key")

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


@pytest.fixture(scope="session", autouse=True)
def install_plugins():
    """Install plugins once per test session for integration tests."""
    import subprocess

    # Try multiple locations where forgesyte-plugins might be
    possible_paths = [
        # Local development
        os.path.join(os.path.expanduser("~"), "forgesyte-plugins", "plugins", "ocr"),
        # CI: sibling directory (GitHub Actions workspace structure)
        os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "forgesyte-plugins",
                "plugins",
                "ocr",
            )
        ),
        # CI: relative from repo root
        os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "..",
                "forgesyte-plugins",
                "plugins",
                "ocr",
            )
        ),
    ]

    for ocr_plugin_path in possible_paths:
        ocr_plugin_path = os.path.abspath(ocr_plugin_path)
        if os.path.isdir(ocr_plugin_path):
            try:
                subprocess.run(
                    ["uv", "pip", "install", "-e", ocr_plugin_path],
                    check=True,
                    timeout=60,
                )
                return  # Success, stop trying
            except Exception:
                continue  # Try next path

    # If we get here, plugin wasn't found - this is OK for some CI environments


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
    from app.plugin_loader import PluginRegistry
    from app.services import (
        PluginManagementService,
        VisionAnalysisService,
    )
    from app.websocket_manager import ws_manager

    # Initialize auth service FIRST (needed for API endpoints)
    init_auth_service()

    # Load plugins via entry-points (OCR plugin installed by install_plugins fixture)
    plugin_manager = PluginRegistry()
    load_result = plugin_manager.load_plugins()
    loaded_list = list(load_result.get("loaded", {}).keys())
    app.state.plugins = plugin_manager

    # Phase 11: Register loaded plugins into health registry (Phase 11 contract)
    from app.plugins.loader.plugin_registry import get_registry

    health_registry = get_registry()
    for plugin_name in loaded_list:
        plugin = plugin_manager.get(plugin_name)
        if plugin:
            # Register plugin in health registry if not already registered
            if health_registry.get_status(plugin_name) is None:
                health_registry.register(
                    plugin_name,
                    getattr(plugin, "description", ""),
                    getattr(plugin, "version", ""),
                    instance=plugin,
                )
                health_registry.mark_initialized(plugin_name)

    # Initialize services
    # Vision analysis service for WebSocket
    app.state.analysis_service = VisionAnalysisService(plugin_manager, ws_manager)
    app.state.plugin_service = PluginManagementService(plugin_manager)

    return app


@pytest.fixture
def app_with_mock_yolo_plugin():
    """Create app with mocked YOLO tracker plugin for GPU integration tests.

    This fixture is specifically for tests that need YOLO plugin without
    requiring real YOLO models to be installed. It injects a mock plugin
    with realistic manifest and tool stubs.

    Returns:
        FastAPI app with mocked yolo-tracker plugin
    """
    from unittest.mock import MagicMock

    from app.auth import init_auth_service
    from app.main import app
    from app.services import (
        PluginManagementService,
        VisionAnalysisService,
    )
    from app.websocket_manager import ws_manager

    # Initialize auth service
    init_auth_service()

    # Create mock plugin registry with YOLO tracker
    mock_registry = MockPluginRegistry()

    # Create a mock YOLO plugin instance
    mock_yolo_plugin = MagicMock()
    mock_yolo_plugin.name = "yolo-tracker"

    # Add realistic metadata for YOLO plugin
    yolo_metadata = {
        "name": "yolo-tracker",
        "version": "1.0.0",
        "description": "YOLO Football Tracker",
    }
    mock_registry.add_plugin("yolo-tracker", yolo_metadata, mock_yolo_plugin)

    app.state.plugins = mock_registry

    # Initialize services
    # Vision analysis service for WebSocket
    app.state.analysis_service = VisionAnalysisService(mock_registry, ws_manager)
    app.state.plugin_service = PluginManagementService(mock_registry)

    return app


@pytest.fixture
async def client(app_with_plugins, session):
    """Create AsyncClient for testing API endpoints.

    This fixture is used for integration tests that need to make actual
    HTTP requests to the FastAPI application.

    Args:
        app_with_plugins: FastAPI app with plugins
        session: Database session for test isolation

    Returns:
        AsyncClient configured with the app_with_plugins app
    """
    from httpx import ASGITransport, AsyncClient

    from app.core.database import get_db

    # Override get_db dependency to use test session
    def override_get_db():
        """Override get_db to use test session."""
        try:
            yield session
        finally:
            pass  # Don't close test session, fixture handles it

    app_with_plugins.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app_with_plugins)
    # Include auth header for integration tests
    headers = {"X-API-Key": os.getenv("FORGESYTE_USER_KEY", "test-user-key")}
    async with AsyncClient(
        transport=transport, base_url="http://test", headers=headers
    ) as async_client:
        yield async_client

    # Clean up dependency overrides
    app_with_plugins.dependency_overrides.clear()


@pytest.fixture
async def client_with_mock_yolo(app_with_mock_yolo_plugin):
    """Create AsyncClient with mocked YOLO plugin for GPU integration tests.

    This fixture uses app_with_mock_yolo_plugin which has a mocked
    yolo-tracker plugin suitable for testing video tracker endpoints
    without requiring real YOLO models.

    Returns:
        AsyncClient configured with mocked YOLO plugin app
    """
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app_with_mock_yolo_plugin)
    headers = {"X-API-Key": os.getenv("FORGESYTE_USER_KEY", "test-user-key")}
    async with AsyncClient(
        transport=transport, base_url="http://test", headers=headers
    ) as async_client:
        yield async_client


# Protocol-based mock fixtures for unit tests
class MockPluginRegistry:
    """Mock PluginRegistry implementing the PluginRegistry Protocol.

    Provides in-memory plugin storage for testing without file system
    dependencies. Satisfies the PluginRegistry Protocol interface.

    Used by: services/plugin_management.py, services/vision_analysis.py
    Tests: tests/services/test_plugin_management.py, tests/websocket/test_streaming.py

    Protocol Compliance:
    - get(name) -> Optional[VisionPlugin]: Returns plugin instance or None
    - list() -> Dict[str, Dict]: Returns all loaded plugins with metadata
    - reload_plugin(name) -> bool: Reloads single plugin (returns success status)
    - reload_all() -> Dict[str, Any]: Reloads all plugins (returns results dict)

    What This Mock Verifies:
    - Plugin lookup by name works correctly
    - Plugin list returns proper metadata format
    - Reload operations complete without errors
    - Plugin instances are properly stored and retrieved
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

    Used by: tasks/task_processor.py, services/job_management.py
    Tests: tests/tasks/test_task_processor.py, tests/services/test_job_management.py

    Protocol Compliance:
    - create(job_id, job_data) -> None: Stores new job record
    - get(job_id) -> Optional[Dict]: Retrieves job by ID
    - update(job_id, updates) -> Optional[Dict]: Updates existing job
    - list_jobs(status, plugin, limit) -> list[Dict]: Lists jobs with optional filters

    What This Mock Verifies:
    - Job creation stores data correctly with proper job_id
    - Job retrieval returns stored data
    - Job updates modify data properly
    - Job listing respects limit parameter
    - Missing jobs return None/empty results
    - Job status and plugin filtering works (when tested)

    Note: The Protocol defines 'create(job_id, job_data)' but this mock has
    'create(plugin_name, request_data)' for convenience. The fixture accepts
    both signatures - see tests using this fixture for actual usage pattern.
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

    Used by: api/jobs.py (REST endpoint), services/analysis.py
    Tests: tests/api/test_jobs.py, tests/services/test_analysis.py

    Protocol Compliance:
    - submit_job(image_bytes, plugin_name, options) -> str: Returns job ID
    - cancel_job(job_id) -> bool: Cancels job, returns success status
    - get_result(job_id) -> Optional[Dict]: Returns job result or None

    What This Mock Verifies:
    - Job submission returns a valid job ID
    - Job results can be retrieved after submission
    - Job cancellation succeeds
    - Missing jobs return None for get_result
    - Callback registration/removal doesn't raise errors

    API Contract Guarantees:
    - POST /v1/jobs returns job_id matching UUID format
    - GET /v1/jobs/{id} returns JobResponse schema (tested in integration tests)
    - Job status transitions: queued -> running -> done/error
    - This mock simplifies to: all jobs complete successfully

    Additional Methods (Protocol Extensions):
    - add_on_complete_callback(callback): Registers completion listener
    - remove_callback(callback): Unregisters completion listener
    - Both are no-ops in mock but present for protocol compatibility
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


# ============================================================================
# Phase 16: Job Model Test Fixtures (DuckDB SQLAlchemy)
# ============================================================================


@pytest.fixture(scope="function")
def test_engine(tmp_path):
    """Create temporary DuckDB engine for tests.

    Uses a function-scoped temporary file to avoid DuckDB native crashes
    during process teardown (SIGABRT on exit).

    Args:
        tmp_path: Pytest's temporary directory fixture

    Returns:
        SQLAlchemy engine for testing
    """
    from sqlalchemy import create_engine

    from app.core.database import Base
    from app.models.job import Job  # noqa: F401 - registers model with Base

    # Create a temporary database file
    db_path = tmp_path / "test.duckdb"
    db_uri = f"duckdb:///{db_path}"

    engine = create_engine(db_uri, future=True)
    Base.metadata.create_all(engine)

    yield engine

    # Explicitly dispose engine before process exit to avoid DuckDB SIGABRT
    engine.dispose()


@pytest.fixture
def session(test_engine):
    """Create a database session for tests.

    Args:
        test_engine: Function-scoped DuckDB engine

    Yields:
        SQLAlchemy session
    """
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=test_engine)
    s = Session()
    yield s
    s.close()


@pytest.fixture(autouse=True)
def mock_session_local(session, monkeypatch):
    """Monkeypatch SessionLocal to use test session.

    Note: We patch SessionLocal for direct usage in submit endpoints,
    but we do NOT patch get_db here. The client fixture handles get_db
    via dependency_overrides, which correctly uses the original function
    reference stored in FastAPI's Depends() objects.

    Args:
        session: Test database session
        monkeypatch: Pytest monkeypatch
    """

    def mock_session_factory():
        return session

    # Patch the module-level SessionLocal directly for all submit endpoints
    monkeypatch.setattr(
        "app.api_routes.routes.video_submit.SessionLocal",
        mock_session_factory,
    )
    monkeypatch.setattr(
        "app.api_routes.routes.image_submit.SessionLocal",
        mock_session_factory,
    )

    # Do NOT patch get_db here - client fixture uses dependency_overrides
    # which correctly overrides the original function reference stored in
    # FastAPI's Depends() objects.
