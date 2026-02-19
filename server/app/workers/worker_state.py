"""Worker state tracking - heartbeat for health checks."""

import time


class WorkerHeartbeat:
    """Track worker heartbeat for health monitoring."""

    def __init__(self):
        self.timestamp = 0.0

    def beat(self) -> None:
        """Record a heartbeat."""
        self.timestamp = time.time()

    def is_recent(self, threshold_seconds: float = 5.0) -> bool:
        """Check if heartbeat is recent (within threshold)."""
        if self.timestamp == 0:
            return False
        return time.time() - self.timestamp < threshold_seconds


worker_last_heartbeat = WorkerHeartbeat()
