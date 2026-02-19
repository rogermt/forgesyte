"""Worker health endpoint."""

from fastapi import APIRouter

from server.app.workers.worker_state import worker_last_heartbeat

router = APIRouter()


@router.get("/v1/worker/health")
def get_worker_health() -> dict:
    """
    Check if the video worker process is alive.

    Returns:
        dict with 'alive' (bool) and 'last_heartbeat' (float timestamp)
    """
    return {
        "alive": worker_last_heartbeat.is_recent(),
        "last_heartbeat": worker_last_heartbeat.timestamp,
    }
