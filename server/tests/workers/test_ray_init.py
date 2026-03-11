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
        # Should have runtime_env with env_vars
        assert "runtime_env" in call_kwargs
        assert "env_vars" in call_kwargs["runtime_env"]

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
        # Should have runtime_env for remote cluster too
        assert "runtime_env" in call_kwargs
        assert "env_vars" in call_kwargs["runtime_env"]

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

    def test_init_ray_injects_runtime_env_with_pythonpath(self):
        """Test that init_ray injects CWD into PYTHONPATH via runtime_env."""
        from app.workers.worker import init_ray

        mock_ray = MagicMock()

        with patch.dict("sys.modules", {"ray": mock_ray}):
            with patch.dict(os.environ, {"PYTHONPATH": "/existing/path"}, clear=False):
                init_ray()

        mock_ray.init.assert_called_once()
        call_kwargs = mock_ray.init.call_args.kwargs

        # Should have runtime_env
        assert "runtime_env" in call_kwargs
        runtime_env = call_kwargs["runtime_env"]

        # Should have env_vars
        assert "env_vars" in runtime_env
        env_vars = runtime_env["env_vars"]

        # PYTHONPATH should include CWD and existing path
        assert "PYTHONPATH" in env_vars
        pythonpath = env_vars["PYTHONPATH"]
        assert "/" in pythonpath  # Contains a path (CWD)
        assert "/existing/path" in pythonpath

    def test_init_ray_syncs_forgesyte_env_vars(self):
        """Test that init_ray passes FORGESYTE_* env vars to Ray workers."""
        from app.workers.worker import init_ray

        mock_ray = MagicMock()

        test_env = {
            "FORGESYTE_CUSTOM": "test_value",
            "PATH": "/usr/bin",
            "UNRELATED_VAR": "should_not_pass",
        }

        with patch.dict("sys.modules", {"ray": mock_ray}):
            with patch.dict(os.environ, test_env, clear=True):
                init_ray()

        call_kwargs = mock_ray.init.call_args.kwargs
        env_vars = call_kwargs["runtime_env"]["env_vars"]

        # Should pass FORGESYTE_* vars
        assert env_vars.get("FORGESYTE_CUSTOM") == "test_value"

        # Should NOT pass unrelated vars OR PATH (PATH overwrites worker node's binary paths)
        assert "UNRELATED_VAR" not in env_vars
        assert "PATH" not in env_vars


class TestWorkerRayIntegration:
    """Tests for worker Ray integration."""

    def test_worker_auto_inits_ray_when_use_ray_true(self):
        """Test worker initializes Ray when use_ray=True."""
        # This is tested indirectly through the run_once tests
        # which mock Ray. Here we just verify the init_ray function exists.
        from app.workers.worker import init_ray

        assert callable(init_ray)
