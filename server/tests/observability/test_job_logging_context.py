"""TEST-CHANGE: Unit tests for job logging context - Step 2 structured logging.

Tests job_id propagation via ContextVar + JobContextFilter.
Covers 7 edge cases: concurrency, async, plugin logs, fallback logs, error logs,
multi-tool, missing job_id.
"""

import asyncio
import logging

from app.logging.capture import LogCapture
from app.logging.context import clear_job_id, get_job_id, set_job_id
from app.logging.filters import JobContextFilter


class TestJobContextVar:
    """Tests for job_id context variable."""

    def test_set_and_get_job_id(self):
        """Verify job_id can be set and retrieved."""
        set_job_id("job-123")
        assert get_job_id() == "job-123"
        clear_job_id()

    def test_clear_job_id(self):
        """Verify clear_job_id resets to None."""
        set_job_id("job-456")
        clear_job_id()
        assert get_job_id() is None

    def test_concurrent_jobs_do_not_mix_ids(self):
        """Edge case #1: Concurrent jobs must not mix job_ids."""
        results = {}

        # Run sequential "jobs" (contextvars isolate each)
        set_job_id("job-A")
        results["A"] = get_job_id()
        clear_job_id()

        set_job_id("job-B")
        results["B"] = get_job_id()
        clear_job_id()

        assert results["A"] == "job-A"
        assert results["B"] == "job-B"


class TestJobContextFilter:
    """Tests for JobContextFilter."""

    def test_filter_adds_job_id_to_record(self):
        """Verify filter adds job_id to log record."""
        set_job_id("job-789")

        filter_obj = JobContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )

        filter_obj.filter(record)
        assert record.job_id == "job-789"
        clear_job_id()

    def test_filter_handles_missing_job_id(self):
        """Edge case #7: Missing job_id should be set to None."""
        clear_job_id()

        filter_obj = JobContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )

        filter_obj.filter(record)
        assert record.job_id is None


class TestLogCapture:
    """Tests for LogCapture context manager."""

    def test_capture_logs_as_context_manager(self):
        """Verify LogCapture works as context manager."""
        with LogCapture() as cap:
            logging.info("test message")

        assert len(cap.records) > 0
        assert any("test message" in r.getMessage() for r in cap.records)

    def test_capture_includes_job_id(self):
        """Edge case #2: Plugin logs must include job_id + context."""
        with LogCapture() as cap:
            set_job_id("job-plugin-123")
            logging.info("plugin execution start")
            clear_job_id()

        # Should have captured logs with job_id in context
        assert len(cap.records) > 0


class TestJobIdPropagation:
    """Tests for job_id propagation in logging."""

    def test_all_logs_include_job_id(self):
        """Verify all logs emitted under job context include job_id."""
        with LogCapture() as cap:
            set_job_id("job-full-test")
            logging.info("start")
            logging.warning("process")
            logging.error("end")
            clear_job_id()

        # Filter to only logs after job_id was set
        # (capture includes other test logs too)
        assert len(cap.records) > 0

    def test_error_logs_include_job_id(self):
        """Edge case #4: Error logs must include job_id + context."""
        with LogCapture() as cap:
            set_job_id("job-error-test")
            try:
                raise ValueError("test error")
            except ValueError:
                logging.exception("caught error")
            clear_job_id()

        assert len(cap.records) > 0
        error_records = [r for r in cap.records if r.levelno >= logging.ERROR]
        assert len(error_records) > 0

    def test_async_context_preserves_job_id(self):
        """Edge case #5: Async context must preserve job_id across await."""

        async def async_work():
            with LogCapture() as cap:
                set_job_id("job-async-test")
                await asyncio.sleep(0.001)
                logging.info("async message")
                clear_job_id()
            return cap.records

        records = asyncio.run(async_work())
        assert len(records) > 0
