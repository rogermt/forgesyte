"""Protocol interfaces for structural typing and abstraction.

This module defines Protocols (structural contracts) that allow components to interact
through well-defined interfaces without tight coupling. Protocols enable dependency
injection, easy testing with mocks, and future extensibility.

Protocols define what methods/attributes an object must have, but don't enforce
inheritance. Any class with the required methods satisfies the protocol.

Examples:
    A PluginRegistry Protocol allows both file-system loaders and database loaders
    to be used interchangeably in the StreamingAnalysisService.

    A KeyRepository Protocol allows testing with in-memory stores without needing
    a real database or environment variables.
"""

from typing import Any, Dict, Optional, Protocol


class VisionPlugin(Protocol):
    """Structural contract for vision analysis plugins.

    Any class with these methods can be used as a vision plugin, enabling
    swappable implementations without code changes.
    """

    def analyze(self, image_bytes: bytes, options: Dict[str, Any]) -> Any:
        """Analyze image and return results.

        Args:
            image_bytes: Raw image bytes (PNG, JPEG, etc.)
            options: Plugin-specific analysis options

        Returns:
            Plugin-specific analysis results (varies by plugin)

        Raises:
            ValueError: If image format is unsupported
            RuntimeError: If analysis fails unexpectedly
        """
        ...

    def metadata(self) -> Dict[str, Any]:
        """Get plugin metadata and capabilities.

        Returns:
            Dictionary with name, description, version, inputs, outputs, permissions

        Raises:
            RuntimeError: If metadata cannot be generated
        """
        ...

    def on_unload(self) -> None:
        """Clean up plugin resources on shutdown.

        Called when server shuts down or plugin is unloaded.
        Should gracefully release any held resources.

        Raises:
            RuntimeError: If cleanup fails
        """
        ...


class PluginRegistry(Protocol):
    """Structural contract for managing modular vision plugins.

    Abstracts the source of plugins (file-system loader, database, remote API, etc.)
    so the analysis service doesn't care where plugins come from.
    """

    def get(self, name: str) -> Optional[VisionPlugin]:
        """Retrieve a loaded plugin by name.

        Args:
            name: Plugin identifier

        Returns:
            Plugin instance if found, None otherwise
        """
        ...

    def list(self) -> Dict[str, Dict[str, Any]]:
        """Get all loaded plugins with their metadata.

        Returns:
            Dictionary mapping plugin names to their metadata dictionaries
        """
        ...

    def reload_plugin(self, name: str) -> bool:
        """Reload a specific plugin to refresh code and state.

        Args:
            name: Plugin identifier

        Returns:
            True if reload succeeded, False if reload failed or plugin not found

        Raises:
            RuntimeError: If reload encounters unexpected errors
        """
        ...

    def reload_all(self) -> Dict[str, Any]:
        """Reload all plugins to refresh code and state.

        Returns:
            Dictionary with reload operation results:
                - success: Boolean indicating overall success
                - reloaded: List of successfully reloaded plugin names
                - failed: List of plugins that failed to reload
                - total: Total number of plugins
                - errors: Optional dict mapping failed plugin names to error messages

        Raises:
            RuntimeError: If reload operation encounters unexpected errors
        """
        ...


class WebSocketProvider(Protocol):
    """Structural contract for real-time WebSocket communication.

    Abstracts message delivery so the analysis service can send results
    without knowing implementation details (queue, broadcast, storage, etc.).
    """

    async def send_personal(self, client_id: str, message: Dict[str, Any]) -> None:
        """Send a message to a specific client.

        Args:
            client_id: Unique client identifier
            message: Message dictionary to send

        Raises:
            RuntimeError: If delivery fails after retries
        """
        ...

    async def send_frame_result(
        self,
        client_id: str,
        frame_id: str,
        plugin: str,
        result: Any,
        time_ms: float,
    ) -> None:
        """Send analysis result for a frame.

        Args:
            client_id: Unique client identifier
            frame_id: Unique frame identifier
            plugin: Plugin that produced result
            result: Analysis result data
            time_ms: Processing time in milliseconds

        Raises:
            RuntimeError: If delivery fails after retries
        """
        ...

    async def disconnect(self, client_id: str) -> None:
        """Clean up client connection.

        Args:
            client_id: Unique client identifier
        """
        ...


class KeyRepository(Protocol):
    """Structural contract for retrieving hashed API keys.

    Abstracts key storage (environment variables, database, cache, etc.)
    so AuthService can validate keys without knowing the source.
    """

    def get_user_by_hash(self, key_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve user information by hashed key.

        Args:
            key_hash: SHA256 hash of API key

        Returns:
            User dictionary with name and permissions if found, None otherwise
                {"name": str, "permissions": list[str]}
        """
        ...


class JobStore(Protocol):
    """Structural contract for job storage and retrieval.

    Abstracts persistence layer (in-memory, database, file system, etc.)
    so task processor can save/load jobs without knowing implementation.
    """

    async def create(self, job_id: str, job_data: Dict[str, Any]) -> None:
        """Create a new job record.

        Args:
            job_id: Unique job identifier
            job_data: Job data dictionary

        Raises:
            RuntimeError: If creation fails
        """
        ...

    async def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a job by ID.

        Args:
            job_id: Unique job identifier

        Returns:
            Job data dictionary if found, None otherwise
        """
        ...

    async def update(self, job_id: str, updates: Dict[str, Any]) -> None:
        """Update an existing job.

        Args:
            job_id: Unique job identifier
            updates: Dictionary of fields to update

        Raises:
            RuntimeError: If update fails
        """
        ...

    async def list_jobs(
        self,
        status: Optional[str] = None,
        plugin: Optional[str] = None,
        limit: int = 50,
    ) -> list[Dict[str, Any]]:
        """List jobs with optional filtering.

        Args:
            status: Filter by job status (optional)
            plugin: Filter by plugin name (optional)
            limit: Maximum number of results

        Returns:
            List of job data dictionaries
        """
        ...


class TaskProcessor(Protocol):
    """Structural contract for background task processing.

    Abstracts job queue implementation so API endpoints can submit work
    without caring how it's executed.
    """

    async def submit_job(
        self, image_bytes: bytes, plugin_name: str, options: Dict[str, Any]
    ) -> str:
        """Submit an analysis job.

        Args:
            image_bytes: Raw image bytes to analyze
            plugin_name: Plugin to use for analysis
            options: Plugin-specific options

        Returns:
            Job ID for tracking

        Raises:
            ValueError: If plugin not found or options invalid
            RuntimeError: If job submission fails
        """
        ...

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued job.

        Args:
            job_id: Unique job identifier

        Returns:
            True if cancelled, False if already running/completed
        """
        ...

    async def get_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis result for a job.

        Args:
            job_id: Unique job identifier

        Returns:
            Job data with result if complete, None if not found
        """
        ...
