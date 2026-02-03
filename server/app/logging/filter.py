"""Logging filter for job correlation.

Injects job_id from context into all log records.
Enables tracing logs across async boundaries and service boundaries.
"""

import logging

from .context import get_job_id


class JobIdFilter(logging.Filter):
    """Adds job_id from context to log records.

    If job_id is set in contextvars, it's added to each log record.
    Logs can then include %(job_id)s in their format string.

    Example:
        logger = logging.getLogger(__name__)
        logger.addFilter(JobIdFilter())
        # Configure formatter with: "[%(job_id)s] %(message)s"

        set_job_id("job-123")
        logger.info("Processing")  # Output: "[job-123] Processing"

        set_job_id(None)
        logger.info("Idle")  # Output: "[None] Idle" or just "Idle"
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add job_id to log record.

        Args:
            record: Log record from logger.

        Returns:
            True (always allow the record through).
        """
        job_id = get_job_id()
        record.job_id = job_id or "-"
        return True
