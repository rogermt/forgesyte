"""Test helper for capturing logs with job_id correlation.

Allows deterministic assertion of logs in tests, including job_id context.
"""

import logging
from contextlib import contextmanager
from typing import Generator, List


class _CaptureHandler(logging.Handler):
    """Custom handler to capture log records."""

    def __init__(self) -> None:
        """Initialize handler."""
        super().__init__()
        self.records: List[logging.LogRecord] = []
        self.messages: List[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Capture the log record."""
        self.records.append(record)
        self.messages.append(record.getMessage())


class LogCapture:
    """Context manager for capturing logs in tests.

    Captures log records with their full context, including job_id.

    Example:
        with LogCapture() as cap:
            logging.info("test message")
            set_job_id("job-123")
            logging.info("with context")

        assert "test message" in cap.messages
        assert any("job-123" in rec for rec in cap.records)
    """

    def __init__(self) -> None:
        """Initialize log capture."""
        self._capture_handler = _CaptureHandler()

    def __enter__(self) -> "LogCapture":
        """Start capturing logs."""
        # Add filter for job_id (if available)
        from app.logging.filter import JobIdFilter

        self._capture_handler.addFilter(JobIdFilter())

        # Get root logger and add handler
        root_logger = logging.getLogger()
        root_logger.addHandler(self._capture_handler)

        # Ensure logs are processed at DEBUG level
        self._old_level = root_logger.level
        root_logger.setLevel(logging.DEBUG)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop capturing logs."""
        root_logger = logging.getLogger()
        root_logger.removeHandler(self._capture_handler)
        root_logger.setLevel(self._old_level)

    @property
    def records(self) -> List[logging.LogRecord]:
        """Get all captured log records.

        Returns:
            List of LogRecord objects (with job_id attribute).
        """
        return self._capture_handler.records

    @property
    def messages(self) -> List[str]:
        """Get all captured log messages.

        Returns:
            List of log message strings.
        """
        return self._capture_handler.messages

    def get_messages(self) -> List[str]:
        """Get all captured log messages.

        Returns:
            List of log message strings.
        """
        return self.messages

    def get_records(self) -> List[logging.LogRecord]:
        """Get all captured log records.

        Returns:
            List of LogRecord objects (with job_id attribute).
        """
        return self.records

    def has_message(self, text: str) -> bool:
        """Check if message was logged.

        Args:
            text: Text to search for in messages.

        Returns:
            True if text found in any message.
        """
        return any(text in msg for msg in self.messages)

    def has_job_id(self, job_id: str) -> bool:
        """Check if job_id appears in any log record.

        Args:
            job_id: Job ID to search for.

        Returns:
            True if job_id found in any record.
        """
        return any(getattr(rec, "job_id", None) == job_id for rec in self.records)


@contextmanager
def capture_logs() -> Generator[LogCapture, None, None]:
    """Context manager for log capture (functional style).

    Example:
        with capture_logs() as cap:
            logging.info("test")
        assert cap.has_message("test")
    """
    cap = LogCapture()
    with cap:
        yield cap
