"""Debug endpoints for database pool monitoring.

Issue #357: DB timeout causing knock-on problems (tools not fetched, jobs stuck).
"""

import time

from fastapi import APIRouter

from ...core.database import engine
from ...workers.db_utils import SESSION_TRACKER, dump_session_map

router = APIRouter(prefix="/v1/debug", tags=["debug"])


@router.get("/db_pool")
def get_db_pool_status() -> dict:
    """Return real-time DB pool status + active session map."""
    pool = engine.pool
    # Pool attributes are methods in SQLAlchemy, need to call them
    size = pool.size() if hasattr(pool, "size") else None
    checked = pool.checkedout() if hasattr(pool, "checkedout") else None
    overflow = pool.overflow() if hasattr(pool, "overflow") else None
    timeout = pool.timeout() if hasattr(pool, "timeout") else None
    now = time.time()
    active_sessions = [
        {
            "thread_id": tid,
            "age_seconds": now - ts,
        }
        for tid, ts in SESSION_TRACKER.items()
    ]
    # Optional: dump to logs when endpoint is hit
    dump_session_map()
    return {
        "pool": {
            "size": size,
            "checked_out": checked,
            "overflow": overflow,
            "timeout": timeout,
        },
        "active_sessions": active_sessions,
    }
