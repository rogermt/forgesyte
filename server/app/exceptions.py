"""Custom exception types for ForgeSyte server.

This module defines domain-specific exceptions that provide semantic meaning
beyond generic Python exceptions. Using specific exceptions allows callers
to handle different error scenarios appropriately and log meaningful context.

Exception Hierarchy:
    ForgeyteError (base)
    ├── AuthenticationError (auth failures)
    ├── AuthorizationError (permission failures)
    ├── ValidationError (data validation failures)
    ├── PluginError (plugin-related failures)
    │   ├── PluginNotFoundError
    │   ├── PluginLoadError
    │   └── PluginExecutionError
    ├── JobError (job processing failures)
    │   ├── JobNotFoundError
    │   ├── JobCancellationError
    │   └── JobExecutionError
    ├── WebSocketError (WebSocket failures)
    └── ExternalServiceError (third-party API failures)

Usage:
    try:
        plugin = registry.get("nonexistent")
    except PluginNotFoundError as e:
        logger.error("Plugin not found", extra={"plugin": e.resource})
        raise HTTPException(404, str(e)) from e
"""


class ForgeyteError(Exception):
    """Base exception for all ForgeSyte-specific errors.

    All custom exceptions inherit from this, allowing callers to catch
    all ForgeSyte errors while letting system errors propagate.
    """

    pass


# Authentication & Authorization Errors


class AuthenticationError(ForgeyteError):
    """Raised when authentication fails (missing or invalid credentials).

    Attributes:
        message: Human-readable error description
        reason: Specific reason for failure ("missing_key", "invalid_key", etc.)
    """

    def __init__(self, message: str, reason: str = "unknown") -> None:
        """Initialize authentication error.

        Args:
            message: Error description
            reason: Specific failure reason
        """
        super().__init__(message)
        self.reason = reason


class AuthorizationError(ForgeyteError):
    """Raised when user lacks required permissions.

    Attributes:
        message: Human-readable error description
        required_permissions: Set of permissions needed
        user_permissions: Set of permissions user has
    """

    def __init__(
        self,
        message: str,
        required_permissions: set[str] | None = None,
        user_permissions: set[str] | None = None,
    ) -> None:
        """Initialize authorization error.

        Args:
            message: Error description
            required_permissions: Permissions needed for operation
            user_permissions: Permissions user currently has
        """
        super().__init__(message)
        self.required_permissions = required_permissions or set()
        self.user_permissions = user_permissions or set()


# Data Validation Errors


class ValidationError(ForgeyteError):
    """Raised when input data fails validation.

    Attributes:
        message: Human-readable error description
        field: Field that failed validation (if applicable)
        value: Value that failed validation
    """

    def __init__(
        self, message: str, field: str | None = None, value: str | None = None
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error description
            field: Field name that failed validation
            value: Value that was invalid
        """
        super().__init__(message)
        self.field = field
        self.value = value


# Plugin Errors


class PluginError(ForgeyteError):
    """Base exception for plugin-related errors.

    Attributes:
        message: Human-readable error description
        plugin_name: Name of the plugin involved
    """

    def __init__(self, message: str, plugin_name: str | None = None) -> None:
        """Initialize plugin error.

        Args:
            message: Error description
            plugin_name: Name of affected plugin
        """
        super().__init__(message)
        self.plugin_name = plugin_name


class PluginNotFoundError(PluginError):
    """Raised when a requested plugin is not loaded.

    Attributes:
        resource: Name of missing plugin
    """

    def __init__(self, plugin_name: str) -> None:
        """Initialize plugin not found error.

        Args:
            plugin_name: Name of missing plugin
        """
        super().__init__(f"Plugin '{plugin_name}' not found", plugin_name)
        self.resource = plugin_name


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load.

    Attributes:
        reason: Specific reason for failure ("syntax_error", "import_error", etc.)
    """

    def __init__(self, plugin_name: str, message: str, reason: str = "unknown") -> None:
        """Initialize plugin load error.

        Args:
            plugin_name: Name of plugin that failed to load
            message: Error description
            reason: Specific failure reason
        """
        super().__init__(message, plugin_name)
        self.reason = reason


class PluginExecutionError(PluginError):
    """Raised when a plugin's analyze() method fails.

    Attributes:
        original_error: The underlying exception from the plugin
    """

    def __init__(
        self, plugin_name: str, message: str, original_error: Exception | None = None
    ) -> None:
        """Initialize plugin execution error.

        Args:
            plugin_name: Name of plugin that failed
            message: Error description
            original_error: Original exception from plugin
        """
        super().__init__(message, plugin_name)
        self.original_error = original_error


# Job Processing Errors


class JobError(ForgeyteError):
    """Base exception for job processing errors.

    Attributes:
        message: Human-readable error description
        job_id: ID of the affected job
    """

    def __init__(self, message: str, job_id: str | None = None) -> None:
        """Initialize job error.

        Args:
            message: Error description
            job_id: ID of affected job
        """
        super().__init__(message)
        self.job_id = job_id


class JobNotFoundError(JobError):
    """Raised when a requested job does not exist.

    Attributes:
        resource: ID of missing job
    """

    def __init__(self, job_id: str) -> None:
        """Initialize job not found error.

        Args:
            job_id: ID of missing job
        """
        super().__init__(f"Job '{job_id}' not found", job_id)
        self.resource = job_id


class JobCancellationError(JobError):
    """Raised when a job cannot be cancelled (already running, completed, etc).

    Attributes:
        reason: Reason why cancellation failed
    """

    def __init__(self, job_id: str, reason: str = "unknown") -> None:
        """Initialize job cancellation error.

        Args:
            job_id: ID of job that could not be cancelled
            reason: Why cancellation failed
        """
        super().__init__(f"Cannot cancel job '{job_id}': {reason}", job_id)
        self.reason = reason


class JobExecutionError(JobError):
    """Raised when job execution fails.

    Attributes:
        phase: Phase of execution that failed ("queued", "running", "storing")
    """

    def __init__(self, job_id: str, message: str, phase: str = "execution") -> None:
        """Initialize job execution error.

        Args:
            job_id: ID of job that failed
            message: Error description
            phase: Phase of execution that failed
        """
        super().__init__(message, job_id)
        self.phase = phase


# WebSocket Errors


class WebSocketError(ForgeyteError):
    """Base exception for WebSocket communication failures.

    Attributes:
        message: Human-readable error description
        client_id: ID of affected client (if applicable)
    """

    def __init__(self, message: str, client_id: str | None = None) -> None:
        """Initialize WebSocket error.

        Args:
            message: Error description
            client_id: ID of affected client
        """
        super().__init__(message)
        self.client_id = client_id


class MessageDeliveryError(WebSocketError):
    """Raised when WebSocket message delivery fails after retries.

    Attributes:
        retry_count: Number of attempts made
    """

    def __init__(self, client_id: str, message: str, retry_count: int = 0) -> None:
        """Initialize message delivery error.

        Args:
            client_id: ID of client that could not receive message
            message: Error description
            retry_count: Number of retry attempts made
        """
        super().__init__(message, client_id)
        self.retry_count = retry_count


# External Service Errors


class ExternalServiceError(ForgeyteError):
    """Raised when an external service call fails (image URL fetch, API call, etc).

    Attributes:
        message: Human-readable error description
        service_name: Name of the external service that failed
        original_error: The underlying exception from the service
    """

    def __init__(
        self,
        message: str,
        service_name: str | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """Initialize external service error.

        Args:
            message: Error description
            service_name: Name of service that failed
            original_error: Original exception from service
        """
        super().__init__(message)
        self.service_name = service_name
        self.original_error = original_error
