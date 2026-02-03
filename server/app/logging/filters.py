"""Logging filter for job context injection.

Adds job_id to every LogRecord for structured logging.
"""

import logging

from app.logging.context import get_job_id


class JobContextFilter(logging.Filter):
    """Filter that injects job_id into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add job_id to the log record."""
        record.job_id = get_job_id()  # type: ignore
        return True
