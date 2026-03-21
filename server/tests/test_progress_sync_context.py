"""Tests for progress broadcast from sync worker context.

Discussion #355: Worker runs in sync thread, must broadcast via main event loop.
"""

from unittest.mock import MagicMock, patch

from app.workers.progress import (
    progress_callback,
    set_main_event_loop,
)


class TestProgressSyncBroadcast:
    """Tests for progress_callback in sync context."""

    def teardown_method(self):
        """Reset module state after each test."""
        import app.workers.progress as progress_module

        progress_module._main_event_loop = None

    def test_progress_callback_returns_event(self):
        """progress_callback always returns a ProgressEvent."""
        event = progress_callback(
            job_id="test-job",
            current_frame=50,
            total_frames=100,
            current_tool="test-tool",
        )

        assert event.job_id == "test-job"
        assert event.current_frame == 50
        assert event.total_frames == 100
        assert event.percent == 50
        assert event.current_tool == "test-tool"

    def test_progress_broadcast_via_main_loop_reference(self):
        """When main loop is set and no running loop, uses run_coroutine_threadsafe."""
        import app.workers.progress as progress_module

        # Mock the main event loop
        mock_loop = MagicMock()
        progress_module._main_event_loop = mock_loop

        # Mock ws_manager.broadcast as async function
        async def mock_broadcast(message, topic=None):
            pass

        # Patch get_running_loop to raise RuntimeError (simulating sync thread)
        with patch("app.workers.progress.asyncio.get_running_loop") as mock_get_loop:
            mock_get_loop.side_effect = RuntimeError("No running loop")

            # Patch run_coroutine_threadsafe to track calls
            with patch(
                "app.workers.progress.asyncio.run_coroutine_threadsafe"
            ) as mock_run:
                with patch("app.workers.progress.ws_manager") as mock_ws:
                    mock_ws.broadcast = mock_broadcast

                    progress_callback(
                        job_id="test-job",
                        current_frame=50,
                        total_frames=100,
                    )

                    # Should have called run_coroutine_threadsafe with our loop
                    assert (
                        mock_run.called
                    ), "run_coroutine_threadsafe should be called when no running loop"
                    # First arg is coroutine, second is the loop
                    call_args = mock_run.call_args
                    assert call_args[0][1] == mock_loop

    def test_set_main_event_loop_stores_reference(self):
        """set_main_event_loop stores the loop for later use."""
        import app.workers.progress as progress_module

        mock_loop = MagicMock()
        set_main_event_loop(mock_loop)

        assert progress_module._main_event_loop == mock_loop
