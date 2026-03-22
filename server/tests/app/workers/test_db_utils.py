"""Tests for database utilities (db_utils.py).

Issue #357: DB timeout causing knock-on problems.
"""

import pytest


@pytest.mark.unit
def test_session_tracker_is_dict():
    """SESSION_TRACKER should be a dictionary for tracking sessions."""
    from app.workers.db_utils import SESSION_TRACKER

    assert isinstance(SESSION_TRACKER, dict)


@pytest.mark.unit
def test_track_session_start_records_thread_id():
    """track_session_start should record current thread ID with timestamp."""
    import threading
    import time

    from app.workers.db_utils import SESSION_TRACKER, track_session_start

    tid = threading.get_ident()
    SESSION_TRACKER.clear()

    track_session_start()

    assert tid in SESSION_TRACKER
    assert isinstance(SESSION_TRACKER[tid], float)
    assert SESSION_TRACKER[tid] <= time.time()

    SESSION_TRACKER.clear()


@pytest.mark.unit
def test_track_session_end_removes_thread_id():
    """track_session_end should remove current thread ID from tracker."""
    import threading

    from app.workers.db_utils import (
        SESSION_TRACKER,
        track_session_end,
        track_session_start,
    )

    SESSION_TRACKER.clear()
    tid = threading.get_ident()

    track_session_start()
    assert tid in SESSION_TRACKER

    track_session_end()
    assert tid not in SESSION_TRACKER


@pytest.mark.unit
def test_track_session_end_handles_missing_id():
    """track_session_end should handle missing thread ID gracefully."""
    from app.workers.db_utils import SESSION_TRACKER, track_session_end

    SESSION_TRACKER.clear()
    # Should not raise
    track_session_end()


@pytest.mark.unit
def test_dump_session_map_logs_sessions(caplog):
    """dump_session_map should log active sessions."""
    import logging

    from app.workers.db_utils import (
        SESSION_TRACKER,
        dump_session_map,
        track_session_start,
    )

    SESSION_TRACKER.clear()
    with caplog.at_level(logging.WARNING):
        track_session_start()
        dump_session_map()

    assert "ACTIVE DB SESSIONS" in caplog.text
    SESSION_TRACKER.clear()
