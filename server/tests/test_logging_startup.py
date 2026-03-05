import importlib
import json
import logging
import os
import sys
from pathlib import Path
from unittest.mock import patch


def _get_log_file_path() -> Path:
    """Get the log file path matching setup_logging logic."""
    working_dir = os.environ.get("KAGGLE_WORKING", os.getcwd())
    return Path(working_dir) / "forgesyte.log"


def test_startup_logging_captured():
    """
    Test that logs from components like storage factory are captured
    when app.main is reloaded with setup_logging at the top.
    """
    # Ensure the 'app' package is in path
    server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if server_dir not in sys.path:
        sys.path.insert(0, server_dir)

    # We MUST reload app.main to trigger the top-level side effects (setup_logging)
    # Using a fresh import if possible or reload
    import app.main

    importlib.reload(app.main)

    root_logger = logging.getLogger()

    # Verify setup_logging() did its job
    assert root_logger.level == logging.DEBUG

    # Check if forgesyte.log was created (use same path logic as setup_logging)
    log_file = _get_log_file_path()
    assert log_file.exists(), f"Log file not found at {log_file}"

    with open(log_file, "r") as f:
        lines = f.readlines()
        found = False
        for line in lines:
            try:
                data = json.loads(line)
                if "ForgeSyte server starting..." in data.get("message", ""):
                    found = True
                    break
            except json.JSONDecodeError:
                if "ForgeSyte server starting..." in line:
                    found = True
                    break
        assert found, f"Startup log not found in {log_file}"


def test_storage_factory_logs_with_captured_logging():
    """
    Verify that storage factory logs are now captured because setup_logging
    happened before router imports.
    """
    import app.main

    importlib.reload(app.main)

    from app.services.storage.factory import _logged_backends, get_storage_service
    from app.settings import AppSettings

    # Reset the logged backends cache to ensure the log message is written
    # (the factory module is not reloaded by importlib.reload(app.main))
    _logged_backends.clear()

    # Create a settings instance to force logging
    with patch.dict(os.environ, {"FORGESYTE_STORAGE_BACKEND": "local"}):
        settings = AppSettings()
        get_storage_service(settings)

    log_file = _get_log_file_path()
    with open(log_file, "r") as f:
        lines = f.readlines()
        found = False
        for line in lines:
            try:
                data = json.loads(line)
                if "Storage Backend: Local Filesystem" in data.get("message", ""):
                    found = True
                    break
            except json.JSONDecodeError:
                if "Storage Backend: Local Filesystem" in line:
                    found = True
                    break
        assert found, f"Storage backend log not found in {log_file}"
