"""Tests for worker state tracking."""

import time

from server.app.workers.worker_state import WorkerHeartbeat


def test_heartbeat_initially_not_recent():
    """Heartbeat should not be recent when first created."""
    hb = WorkerHeartbeat()
    assert not hb.is_recent()


def test_heartbeat_beat_sets_timestamp():
    """Calling beat() should set timestamp."""
    hb = WorkerHeartbeat()
    hb.beat()
    assert hb.timestamp > 0


def test_heartbeat_is_recent_after_beat():
    """Heartbeat should be recent immediately after beat()."""
    hb = WorkerHeartbeat()
    hb.beat()
    assert hb.is_recent()


def test_heartbeat_expires_after_threshold():
    """Heartbeat should expire after threshold seconds."""
    hb = WorkerHeartbeat()
    hb.beat()
    assert hb.is_recent(threshold_seconds=0.1)

    time.sleep(0.2)
    assert not hb.is_recent(threshold_seconds=0.1)


def test_heartbeat_custom_threshold():
    """Heartbeat threshold should be configurable."""
    hb = WorkerHeartbeat()
    hb.beat()

    # Recent with 10 second threshold
    assert hb.is_recent(threshold_seconds=10.0)

    # Still recent with 1 second threshold
    assert hb.is_recent(threshold_seconds=1.0)
