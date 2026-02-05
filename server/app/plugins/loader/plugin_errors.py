"""Plugin error types for Phase 11.

Structured error types for plugin loading and execution failures.
"""


class PluginError(Exception):
    """Base exception for plugin-related errors."""

    pass


class PluginLoadError(PluginError):
    """Exception raised when plugin fails to load."""

    pass


class PluginImportError(PluginLoadError):
    """Exception raised when plugin module cannot be imported."""

    pass


class PluginInitError(PluginLoadError):
    """Exception raised when plugin initialization fails."""

    pass


class PluginDependencyError(PluginLoadError):
    """Exception raised when plugin dependencies are missing."""

    pass


class PluginValidationError(PluginLoadError):
    """Exception raised when plugin validation fails."""

    pass


class PluginExecutionError(PluginError):
    """Exception raised when plugin execution fails."""

    pass


class PluginTimeoutError(PluginExecutionError):
    """Exception raised when plugin execution times out."""

    pass


class PluginMemoryError(PluginExecutionError):
    """Exception raised when plugin exceeds memory limits."""

    pass
