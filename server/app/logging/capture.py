"""LogCapture helper for test assertions on logs.

Context manager that captures all log records emitted during its scope.
Used for ForgeSyte logging tests (job_id propagation, plugin logs, fallback logs).
"""

import logging


class LogCapture:
    """
    Context manager that captures all log records emitted during its scope.

    Used for ForgeSyte logging tests (job_id propagation, plugin logs, fallback logs).
    """

    def __init__(self):
        self.records = []
        self._handler = None
        self._filter = None

    def __enter__(self):
        from app.logging.filters import JobContextFilter

        self._handler = _CaptureHandler(self.records)
        self._handler.setLevel(logging.DEBUG)  # Capture all levels

        # Add filter to inject job_id
        self._filter = JobContextFilter()
        self._handler.addFilter(self._filter)

        # Add handler to root logger
        root = logging.getLogger()
        root.addHandler(self._handler)
        # Also ensure root logger is at DEBUG level during capture
        old_level = root.level
        self._old_level = old_level
        root.setLevel(logging.DEBUG)

        return self

    def __exit__(self, exc_type, exc, tb):
        root = logging.getLogger()
        root.removeHandler(self._handler)
        root.setLevel(self._old_level)
        self._handler = None
        self._filter = None


class _CaptureHandler(logging.Handler):
    """Internal handler that stores LogRecord objects."""

    def __init__(self, store):
        super().__init__()
        self.store = store

    def emit(self, record):
        self.store.append(record)
