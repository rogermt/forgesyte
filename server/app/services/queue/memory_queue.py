"""In-memory FIFO queue implementation."""

import queue
from typing import Optional

from app.services.queue.base import QueueService


class InMemoryQueueService(QueueService):
    """Thread-safe FIFO queue using Python's queue.Queue.

    Strictly accepts and returns job_id (UUID string) payloads.
    """

    def __init__(self) -> None:
        """Initialize the in-memory queue."""
        self._queue: queue.Queue[str] = queue.Queue()

    def enqueue(self, job_id: str) -> None:
        """Add a job_id to the queue.

        Args:
            job_id: UUID string identifying the job
        """
        self._queue.put(job_id)

    def dequeue(self) -> Optional[str]:
        """Remove and return the next job_id from the queue.

        Returns:
            Job ID string, or None if queue is empty
        """
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def size(self) -> int:
        """Return the current number of items in the queue.

        Returns:
            Queue size
        """
        return self._queue.qsize()
