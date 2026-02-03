"""Job ID correlation context using contextvars.

Propagates job_id through the entire request lifecycle for logging correlation.
All logs within a job context automatically include the job_id.
"""

import contextvars
from typing import Optional

# ContextVar for job_id propagation
_job_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "job_id", default=None
)


def set_job_id(job_id: str) -> None:
    """Set job_id for current context.

    Args:
        job_id: Unique job identifier to propagate in logs.

    Example:
        set_job_id("abc-123-def")
        logging.info("Processing started")  # Will include [job_id=abc-123-def]
    """
    _job_id_var.set(job_id)


def get_job_id() -> Optional[str]:
    """Get job_id from current context.

    Returns:
        Job ID if set, None otherwise.

    Example:
        job_id = get_job_id()
        if job_id:
            logging.info(f"Job: {job_id}")
    """
    return _job_id_var.get()


def clear_job_id() -> None:
    """Clear job_id from current context.

    Used in cleanup code or test teardown.
    """
    _job_id_var.set(None)
