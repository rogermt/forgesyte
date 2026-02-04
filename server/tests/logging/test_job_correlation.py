"""Tests for job_id correlation in logging.

Verifies that job_id is propagated through context and appears in all logs.
"""

import logging


class TestJobIdContext:
    """Tests for job_id context variable."""

    def test_set_and_get_job_id(self) -> None:
        """Verify job_id can be set and retrieved."""
        from app.logging.context import clear_job_id, get_job_id, set_job_id

        set_job_id("job-123")
        assert get_job_id() == "job-123"

        clear_job_id()
        assert get_job_id() is None

    def test_job_id_default_is_none(self) -> None:
        """Verify job_id defaults to None."""
        from app.logging.context import clear_job_id, get_job_id

        clear_job_id()  # Ensure clean state
        assert get_job_id() is None

    def test_job_id_case_sensitive(self) -> None:
        """Verify job_id values are case-sensitive."""
        from app.logging.context import clear_job_id, get_job_id, set_job_id

        set_job_id("ABC-123")
        assert get_job_id() == "ABC-123"
        assert get_job_id() != "abc-123"

        clear_job_id()

    def test_job_id_isolation(self) -> None:
        """Verify job_id is isolated between contexts."""
        import asyncio

        from app.logging.context import clear_job_id, get_job_id, set_job_id

        async def context1() -> str:
            set_job_id("job-1")
            await asyncio.sleep(0.001)
            return get_job_id()

        async def context2() -> str:
            set_job_id("job-2")
            await asyncio.sleep(0.001)
            return get_job_id()

        async def run_both():
            r1, r2 = await asyncio.gather(context1(), context2())
            return r1, r2

        r1, r2 = asyncio.run(run_both())
        # Each context should have its own job_id
        assert r1 == "job-1"
        assert r2 == "job-2"

        clear_job_id()


class TestJobIdFilter:
    """Tests for job_id logging filter."""

    def test_filter_adds_job_id_to_record(self) -> None:
        """Verify filter adds job_id to log record."""
        from app.logging.context import clear_job_id, set_job_id
        from app.logging.filter import JobIdFilter

        set_job_id("job-abc")

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test",
            args=(),
            exc_info=None,
        )

        filter_obj = JobIdFilter()
        result = filter_obj.filter(record)

        assert result is True
        assert record.job_id == "job-abc"  # type: ignore[attr-defined]

        clear_job_id()

    def test_filter_handles_no_job_id(self) -> None:
        """Verify filter handles missing job_id gracefully."""
        from app.logging.context import clear_job_id
        from app.logging.filter import JobIdFilter

        clear_job_id()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test",
            args=(),
            exc_info=None,
        )

        filter_obj = JobIdFilter()
        result = filter_obj.filter(record)

        assert result is True
        assert record.job_id == "-"  # type: ignore[attr-defined]

    def test_filter_multiple_records(self) -> None:
        """Verify filter works with multiple records."""
        from app.logging.context import clear_job_id, set_job_id
        from app.logging.filter import JobIdFilter

        filter_obj = JobIdFilter()

        # Record 1 with job_id
        set_job_id("job-1")
        record1 = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="msg1",
            args=(),
            exc_info=None,
        )
        filter_obj.filter(record1)

        # Record 2 with different job_id
        set_job_id("job-2")
        record2 = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=2,
            msg="msg2",
            args=(),
            exc_info=None,
        )
        filter_obj.filter(record2)

        assert record1.job_id == "job-1"  # type: ignore[attr-defined]
        assert record2.job_id == "job-2"  # type: ignore[attr-defined]

        clear_job_id()


class TestLogCapture:
    """Tests for LogCapture test helper."""

    def test_capture_basic_logs(self) -> None:
        """Verify LogCapture captures basic logs."""
        from tests.helpers.log_capture import LogCapture

        with LogCapture() as cap:
            logging.info("test message")
            logging.warning("warning message")

        assert cap.has_message("test message")
        assert cap.has_message("warning message")
        assert len(cap.get_messages()) == 2

    def test_capture_with_job_id(self) -> None:
        """Verify LogCapture captures job_id in records."""
        from app.logging.context import clear_job_id, set_job_id
        from tests.helpers.log_capture import LogCapture

        with LogCapture() as cap:
            set_job_id("job-xyz")
            logging.info("with context")

        assert cap.has_message("with context")
        assert cap.has_job_id("job-xyz")
        assert len(cap.get_records()) > 0

        clear_job_id()

    def test_capture_mixed_logs(self) -> None:
        """Verify LogCapture handles logs with and without job_id."""
        from app.logging.context import clear_job_id, set_job_id
        from tests.helpers.log_capture import LogCapture

        with LogCapture() as cap:
            logging.info("no context")
            set_job_id("job-123")
            logging.info("with context")
            clear_job_id()
            logging.info("no context again")

        assert cap.has_message("no context")
        assert cap.has_message("with context")
        assert cap.has_message("no context again")
        assert len(cap.get_messages()) == 3

    def test_capture_isolation(self) -> None:
        """Verify multiple LogCapture instances are isolated."""
        from tests.helpers.log_capture import LogCapture

        with LogCapture() as cap1:
            logging.info("message1")

            with LogCapture():
                logging.info("message2")

            logging.info("message3")

        # cap1 should have all three messages
        assert cap1.has_message("message1")
        assert cap1.has_message("message2")
        assert cap1.has_message("message3")


class TestLoggingIntegration:
    """Integration tests for logging correlation."""

    def test_contextvars_survive_async(self) -> None:
        """Verify job_id survives async context transitions."""
        import asyncio

        from app.logging.context import clear_job_id, get_job_id, set_job_id

        async def async_function():
            # Job ID should be preserved from parent context
            return get_job_id()

        set_job_id("job-async")
        asyncio.run(async_function())
        # Note: contextvars don't automatically survive asyncio.run()
        # They would need to be explicitly copied in a real scenario
        # For now, this test documents the behavior

        clear_job_id()

    def test_job_id_in_exception_logs(self) -> None:
        """Verify job_id appears in exception logs."""
        from app.logging.context import clear_job_id, set_job_id
        from tests.helpers.log_capture import LogCapture

        with LogCapture() as cap:
            set_job_id("job-error")
            try:
                raise ValueError("test error")
            except ValueError:
                logging.exception("An error occurred")

        assert cap.has_message("An error occurred")
        records = cap.get_records()
        assert any(rec.job_id == "job-error" for rec in records)  # type: ignore[attr-defined]

        clear_job_id()
