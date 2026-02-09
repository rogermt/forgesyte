"""Test server startup with correct module import paths.

Tests that the server can be started without ModuleNotFoundError
when uvicorn loads the app module string.
"""

from unittest.mock import patch

import pytest


def test_uvicorn_app_module_string_is_valid():
    """Test that uvicorn.run() receives valid module import string.

    When server is started with:
        cd server && uv run python -m app.main

    The uvicorn.run("app.main:app") should be valid, not "server.app.main:app".
    """
    from app.main import run_server

    # Mock uvicorn.run to capture the app string
    with patch("app.main.uvicorn.run") as mock_run:
        with pytest.raises(SystemExit):
            run_server(host="0.0.0.0", port=8000, reload=False)

        # Verify uvicorn.run was called
        mock_run.assert_called_once()

        # Get the app string argument
        call_args = mock_run.call_args
        app_string = call_args[0][0]  # First positional arg

        # Should be "app.main:app", NOT "server.app.main:app"
        assert app_string == "app.main:app", (
            f"Expected 'app.main:app', got '{app_string}'. "
            "This causes ModuleNotFoundError when server runs from cd server/"
        )


def test_app_module_is_importable():
    """Test that app.main module can be imported (required for uvicorn)."""
    # This should not raise ModuleNotFoundError
    from app import main as app_module

    assert hasattr(app_module, "app"), "app.main module should have 'app' object"
    assert hasattr(app_module, "run_server"), "app.main module should have run_server()"
