"""Abstract queue service interface."""

from abc import ABC, abstractmethod
from typing import Optional


class QueueService(ABC):
    """Abstract queue interface for Phase 16 job processing.

    Queues accept strictly job_id (UUID string) payloads.
    """

    @abstractmethod
    def enqueue(self, job_id: str) -> None:
        """Add a job_id to the queue.

        Args:
            job_id: UUID string identifying the job

        Raises:
            ValueError: If job_id is not a valid UUID string
        """
        raise NotImplementedError

    @abstractmethod
    def dequeue(self) -> Optional[str]:
        """Remove and return the next job_id from the queue.

        Returns:
            Job ID string, or None if queue is empty
        """
        raise NotImplementedError

    @abstractmethod
    def size(self) -> int:
        """Return the current number of items in the queue.

        Returns:
            Queue size
        """
        raise NotImplementedError
