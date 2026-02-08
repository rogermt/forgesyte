"""TEST-CHANGE: Test for Issue #164 — image_bytes key contract.

Verifies that all code paths construct tool_args with the correct key name
("image_bytes", not "image") when executing plugins.

This test demonstrates the regression where multiple code paths were passing
tool_args with the wrong key, causing plugins to fail with:
    ValueError: image_bytes must be bytes
"""

from unittest.mock import MagicMock, patch

import pytest


class TestIssue164ToolArgsContract:
    """Tests for Issue #164: All execution paths must use 'image_bytes' key."""

    def test_tasks_py_uses_image_bytes_key(self):
        """
        Issue #164: tasks.py must use 'image_bytes' key in tool_args.
        """
        with open("/home/rogermt/forgesyte/server/app/tasks.py") as f:
            content = f.read()

        # Assert wrong key is NOT present
        assert '"image": image_bytes' not in content, (
            "tasks.py line 389: Found forbidden pattern '\"image\": image_bytes'. "
            "Use '\"image_bytes\": image_bytes' instead."
        )

        # Assert correct key IS present in _process_job context
        assert '"image_bytes": image_bytes' in content, (
            "tasks.py: Expected '\"image_bytes\": image_bytes' in tool_args. "
            "This is the required plugin contract key."
        )

    def test_vision_analysis_uses_image_bytes_key(self):
        """
        Issue #164: vision_analysis.py must use 'image_bytes' key in tool_args.
        """
        with open("/home/rogermt/forgesyte/server/app/services/vision_analysis.py") as f:
            content = f.read()

        # Assert wrong key is NOT present
        assert '"image": image_bytes' not in content, (
            "vision_analysis.py: Found forbidden pattern '\"image\": image_bytes'. "
            "Use '\"image_bytes\": image_bytes' instead."
        )

        # Assert correct key IS present
        assert '"image_bytes": image_bytes' in content, (
            "vision_analysis.py: Expected '\"image_bytes\": image_bytes' in tool_args. "
            "This is the required plugin contract key."
        )

    def test_mcp_handlers_uses_image_bytes_key(self):
        """
        Issue #164: mcp/handlers.py must use 'image_bytes' key in tool_args.
        """
        with open("/home/rogermt/forgesyte/server/app/mcp/handlers.py") as f:
            content = f.read()

        # Assert wrong key is NOT present
        assert '"image": image_bytes' not in content, (
            "mcp/handlers.py: Found forbidden pattern '\"image\": image_bytes'. "
            "Use '\"image_bytes\": image_bytes' instead."
        )

        # Assert correct key IS present
        assert '"image_bytes": image_bytes' in content, (
            "mcp/handlers.py: Expected '\"image_bytes\": image_bytes' in tool_args. "
            "This is the required plugin contract key."
        )

    def test_no_image_key_anywhere_in_pipeline(self):
        """
        Issue #164: Ensure no execution path uses bare 'image' key.

        Scans all relevant execution modules to prevent regression.
        """
        files_to_check = [
            "/home/rogermt/forgesyte/server/app/tasks.py",
            "/home/rogermt/forgesyte/server/app/services/vision_analysis.py",
            "/home/rogermt/forgesyte/server/app/mcp/handlers.py",
            "/home/rogermt/forgesyte/server/app/services/analysis_service.py",
        ]

        for filepath in files_to_check:
            try:
                with open(filepath) as f:
                    content = f.read()

                # Forbidden patterns
                forbidden = [
                    '"image": image_bytes',
                    "'image': image_bytes",
                ]

                for pattern in forbidden:
                    assert pattern not in content, (
                        f"{filepath}: Found forbidden key pattern '{pattern}'. "
                        f"All plugins expect 'image_bytes', not 'image'."
                    )
            except FileNotFoundError:
                pytest.skip(f"File not found: {filepath}")
