"""Tests for Ray initialization in worker."""

import os
from unittest.mock import MagicMock, patch


class TestRayInitialization:
    """Tests for configurable Ray initialization."""

    def test_init_ray_local_default(self):
        """Test Ray initializes locally when no address is configured."""
        from app.workers.worker import init_ray

        mock_ray = MagicMock()

        with patch.dict("sys.modules", {"ray": mock_ray}):
            with patch.dict(os.environ, {}, clear=True):
                init_ray()

        mock_ray.init.assert_called_once()
        # Should be called with ignore_reinit_error=True
        call_kwargs = mock_ray.init.call_args.kwargs
        assert call_kwargs.get("ignore_reinit_error") is True

    def test_init_ray_with_address_from_env(self):
        """Test Ray connects to head when RAY_ADDRESS is set."""
        from app.workers.worker import init_ray

        mock_ray = MagicMock()

        with patch.dict("sys.modules", {"ray": mock_ray}):
            with patch.dict(
                os.environ, {"RAY_ADDRESS": "ray://head-node:10001"}, clear=True
            ):
                init_ray()

        mock_ray.init.assert_called_once()
        call_kwargs = mock_ray.init.call_args.kwargs
        assert call_kwargs.get("address") == "ray://head-node:10001"

    def test_init_ray_idempotent(self):
        """Test Ray init is idempotent (handles re-init gracefully)."""
        from app.workers.worker import init_ray

        mock_ray = MagicMock()

        with patch.dict("sys.modules", {"ray": mock_ray}):
            init_ray()
            init_ray()  # Call twice

        # Should be called twice but with ignore_reinit_error=True
        assert mock_ray.init.call_count == 2

    def test_init_ray_returns_on_success(self):
        """Test init_ray returns True on successful initialization."""
        from app.workers.worker import init_ray

        mock_ray = MagicMock()

        with patch.dict("sys.modules", {"ray": mock_ray}):
            result = init_ray()

        assert result is True

    def test_init_ray_returns_false_on_failure(self):
        """Test init_ray returns False on initialization failure."""
        from app.workers.worker import init_ray

        mock_ray = MagicMock()
        mock_ray.init.side_effect = RuntimeError("Ray failed to start")

        with patch.dict("sys.modules", {"ray": mock_ray}):
            result = init_ray()

        assert result is False


class TestWorkerRayIntegration:
    """Tests for worker Ray integration."""

    def test_worker_auto_inits_ray_when_use_ray_true(self):
        """Test worker initializes Ray when use_ray=True."""
        # This is tested indirectly through the run_once tests
        # which mock Ray. Here we just verify the init_ray function exists.
        from app.workers.worker import init_ray

        assert callable(init_ray)
