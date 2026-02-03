"""Job ID context variable for structured logging.

Uses Python's contextvars for async-safe job_id propagation.
"""

from contextvars import ContextVar

# ContextVar for job_id (thread-safe, async-safe)
_job_id_var: ContextVar[str | None] = ContextVar("job_id", default=None)


def set_job_id(job_id: str) -> None:
    """Set the current job_id in context."""
    _job_id_var.set(job_id)


def get_job_id() -> str | None:
    """Get the current job_id from context."""
    return _job_id_var.get()


def clear_job_id() -> None:
    """Clear the job_id from context."""
    _job_id_var.set(None)
