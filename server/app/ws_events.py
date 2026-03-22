"""WebSocket event broadcasting helpers.

Issue #357: DB timeout causing knock-on problems.
"""

import asyncio
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


async def broadcast_event(event_type: str, data: Dict[str, Any]) -> None:
    """Broadcast an event to all connected WebSocket clients."""
    try:
        from app.websocket_manager import ws_manager

        message = {
            "type": event_type,
            **data,
        }
        await ws_manager.broadcast(message)
    except Exception as e:
        logger.error(f"[WS-EVENTS] Failed to broadcast {event_type}: {e}")


def send_db_health(status: str, data: Dict[str, Any]) -> None:
    """Send DB health status via WebSocket broadcast.

    Args:
        status: "warning" or "critical"
        data: Pool status data dict
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(broadcast_event("db_health", {"status": status, "data": data}))
    except RuntimeError:
        # No running loop - this is sync context
        logger.warning(f"[DB-HEALTH] {status}: {data}")


def send_job_completed(job_id: str) -> None:
    """Broadcast job completed event."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(broadcast_event("job_completed", {"job_id": job_id}))
    except RuntimeError:
        logger.info(f"[JOB-COMPLETED] Job {job_id} completed")
