"""Device usage tracking and metrics logging.

Logs device selection decisions to the device_usage table for observability.
Tracks both requested and actual device usage with fallback detection.
"""

import logging
import uuid
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class DeviceTracker:
    """Track device selection and fallback decisions."""

    def __init__(self, duckdb_manager: Any) -> None:
        """Initialize device tracker with DuckDB connection.

        Args:
            duckdb_manager: DuckDB manager instance for metrics logging.
        """
        self.db = duckdb_manager
        logger.debug("DeviceTracker initialized")

    async def log_device_usage(
        self,
        job_id: str,
        device_requested: str,
        device_used: str,
    ) -> None:
        """Log device usage to device_usage table.

        Args:
            job_id: Unique job identifier.
            device_requested: Device requested by user (cpu or gpu).
            device_used: Device actually used (cpu or gpu).

        Raises:
            RuntimeError: If database write fails.
        """
        try:
            # Determine if fallback occurred
            fallback = (
                device_requested.lower() == "gpu" and device_used.lower() == "cpu"
            )

            # Insert into device_usage table
            query = """
            INSERT INTO device_usage
            (id, job_id, device_requested, device_used, fallback, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """

            self.db.execute(
                query,
                [
                    str(uuid.uuid4()),
                    job_id,
                    device_requested.lower(),
                    device_used.lower(),
                    fallback,
                    datetime.utcnow(),
                ],
            )

            logger.info(
                "Device usage logged",
                extra={
                    "job_id": job_id,
                    "device_requested": device_requested.lower(),
                    "device_used": device_used.lower(),
                    "fallback": fallback,
                },
            )

        except Exception as e:
            logger.error(
                "Failed to log device usage",
                extra={
                    "job_id": job_id,
                    "device_requested": device_requested,
                    "device_used": device_used,
                    "error": str(e),
                },
            )
            raise RuntimeError(f"Failed to log device usage: {e}") from e

    async def get_device_stats(self) -> dict[str, Any]:
        """Get device usage statistics.

        Returns:
            Dictionary with device usage stats:
                - total_jobs: Total jobs processed
                - cpu_jobs: Jobs run on CPU
                - gpu_jobs: Jobs run on GPU
                - fallback_count: Jobs that fell back from GPU to CPU
                - gpu_success_rate: Percentage of GPU jobs without fallback

        Raises:
            RuntimeError: If query fails.
        """
        try:
            result = self.db.execute(
                """
                SELECT
                    COUNT(*) as total_jobs,
                    COUNT(CASE WHEN device_used = 'cpu' THEN 1 END) as cpu_jobs,
                    COUNT(CASE WHEN device_used = 'gpu' THEN 1 END) as gpu_jobs,
                    COUNT(CASE WHEN fallback = true THEN 1 END) as fallback_count
                FROM device_usage
                """
            ).fetchall()

            if not result:
                return {
                    "total_jobs": 0,
                    "cpu_jobs": 0,
                    "gpu_jobs": 0,
                    "fallback_count": 0,
                    "gpu_success_rate": 0.0,
                }

            row = result[0]
            total = row[0]
            cpu = row[1]
            gpu = row[2]
            fallback = row[3]

            # GPU success rate = GPU jobs without fallback
            gpu_without_fallback = max(0, gpu - fallback)
            gpu_success_rate = (gpu_without_fallback / gpu * 100) if gpu > 0 else 0.0

            stats = {
                "total_jobs": total,
                "cpu_jobs": cpu,
                "gpu_jobs": gpu,
                "fallback_count": fallback,
                "gpu_success_rate": gpu_success_rate,
            }

            logger.info(
                "Device statistics",
                extra=stats,
            )

            return stats

        except Exception as e:
            logger.error(
                "Failed to get device statistics",
                extra={"error": str(e)},
            )
            raise RuntimeError(f"Failed to get device statistics: {e}") from e
