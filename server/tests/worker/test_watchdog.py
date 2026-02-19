"""Tests for watchdog auto-restart logic."""

from unittest.mock import MagicMock, patch

from server.app.workers.watchdog import start_worker


def test_start_worker_returns_process():
    """Verify start_worker returns a Popen object."""
    with patch("server.app.workers.watchdog.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc

        proc = start_worker()

        assert proc is not None
        mock_popen.assert_called_once()


def test_start_worker_uses_correct_script():
    """Verify watchdog runs the correct worker script."""
    with patch("server.app.workers.watchdog.subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc

        start_worker()

        # Check that the call includes the worker script path
        call_args = mock_popen.call_args
        cmd_list = call_args[0][0]
        assert any("run_video_worker.py" in str(arg) for arg in cmd_list)
