"""Database utilities for session tracking and debugging.

Issue #357: DB timeout causing knock-on problems (tools not fetched, jobs stuck).
"""

import logging
import threading
import time
import traceback

from app.core.database import engine
from app.ws_events import send_db_health

logger = logging.getLogger(__name__)

SESSION_TRACKER: dict[int, float] = {}
SESSION_WARN_THRESHOLD = 10  # seconds


def log_pool_status(tag: str = "") -> None:
    try:
        pool = engine.pool
        # Pool attributes are methods in SQLAlchemy, need to call them
        size = pool.size() if hasattr(pool, "size") else None
        checked = pool.checkedout() if hasattr(pool, "checkedout") else None
        overflow = pool.overflow() if hasattr(pool, "overflow") else None
        timeout = pool.timeout() if hasattr(pool, "timeout") else None
        logger.warning(
            "[DB-POOL] %s size=%s checked_out=%s overflow=%s timeout=%s",
            tag,
            size,
            checked,
            overflow,
            timeout,
        )
    except Exception as e:
        logger.error(f"[DB-POOL] Failed to inspect pool: {e}")


def alarm_if_pool_exhausted(tag: str = "") -> None:
    try:
        pool = engine.pool
        # Pool attributes are methods in SQLAlchemy, need to call them
        size = pool.size() if hasattr(pool, "size") else None
        checked = pool.checkedout() if hasattr(pool, "checkedout") else None
        overflow = pool.overflow() if hasattr(pool, "overflow") else None
        timeout = pool.timeout() if hasattr(pool, "timeout") else None

        if size is None or checked is None:
            return

        if checked >= size * 0.8 or (overflow and overflow > 0):
            status = "warning" if checked < size else "critical"

            send_db_health(
                status,
                {
                    "tag": tag,
                    "size": size,
                    "checked_out": checked,
                    "overflow": overflow,
                    "timeout": timeout,
                },
            )

            logger.error(
                "\n🔥 DB POOL EXHAUSTION WARNING 🔥\n"
                f"Tag: {tag}\n"
                f"Pool size={size}, checked_out={checked}, overflow={overflow}, timeout={timeout}\n"
                f"Stack:\n{''.join(traceback.format_stack())}\n"
            )
    except Exception as e:
        logger.error(f"[POOL-ALARM] Failed to inspect pool: {e}")


def adaptive_backoff() -> None:
    try:
        pool = engine.pool
        # Pool attributes are methods in SQLAlchemy, need to call them
        checked = pool.checkedout() if hasattr(pool, "checkedout") else 0
        size = pool.size() if hasattr(pool, "size") else 1
    except Exception:
        return

    if size <= 0:
        return

    ratio = checked / size
    if ratio < 0.5:
        return
    elif ratio < 0.8:
        time.sleep(0.2)
    elif ratio < 1.0:
        time.sleep(0.5)
    else:
        time.sleep(1.0)


def track_session_start() -> None:
    tid = threading.get_ident()
    SESSION_TRACKER[tid] = time.time()


def track_session_end() -> None:
    tid = threading.get_ident()
    start = SESSION_TRACKER.pop(tid, None)
    if start is None:
        return
    age = time.time() - start
    if age > SESSION_WARN_THRESHOLD:
        logger.error(
            f"⚠️ SESSION LEAK WARNING: Thread {tid} held DB session for {age:.2f}s"
        )


def dump_session_map() -> None:
    now = time.time()
    logger.warning("=== ACTIVE DB SESSIONS ===")
    for tid, ts in SESSION_TRACKER.items():
        age = now - ts
        logger.warning(f"Thread {tid} holding session for {age:.2f}s")
    logger.warning("==========================")
