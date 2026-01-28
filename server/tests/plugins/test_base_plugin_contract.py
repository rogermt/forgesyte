"""Tests for BasePlugin contract enforcement with metadata-based tools."""

import pytest

from app.plugins.base import BasePlugin


def test_valid_plugin_with_metadata_tools():
    """Verify plugin with valid metadata tools loads."""

    class GoodPlugin(BasePlugin):
        name = "good"

        def __init__(self):
            self.tools = {
                "detect": {
                    "handler": self.detect,
                    "description": "Detect things",
                    "input_schema": {"frame": {"type": "string"}},
                    "output_schema": {"result": {"type": "object"}},
                }
            }
            super().__init__()

        def detect(self, frame: str):
            return {"result": {}}

        def run_tool(self, tool_name: str, args: dict):
            meta = self.tools[tool_name]
            return meta["handler"](**args)

    plugin = GoodPlugin()
    assert plugin.name == "good"
    assert "detect" in plugin.tools


def test_missing_handler_rejected():
    """Verify tool without handler is rejected."""

    class BadPlugin(BasePlugin):
        name = "bad"

        def __init__(self):
            self.tools = {
                "detect": {
                    # missing handler
                    "description": "Detect things",
                    "input_schema": {},
                    "output_schema": {},
                }
            }
            super().__init__()

        def run_tool(self, tool_name: str, args: dict):
            pass

    with pytest.raises(ValueError, match="handler"):
        BadPlugin()


def test_non_callable_handler_rejected():
    """Verify tool with non-callable handler is rejected."""

    class BadPlugin(BasePlugin):
        name = "bad"

        def __init__(self):
            self.tools = {
                "detect": {
                    "handler": "not_callable",
                    "description": "Detect things",
                    "input_schema": {},
                    "output_schema": {},
                }
            }
            super().__init__()

        def run_tool(self, tool_name: str, args: dict):
            pass

    with pytest.raises(ValueError, match="handler"):
        BadPlugin()


def test_missing_description_rejected():
    """Verify tool without description is rejected."""

    class BadPlugin(BasePlugin):
        name = "bad"

        def __init__(self):
            self.tools = {
                "detect": {
                    "handler": lambda: None,
                    # missing description
                    "input_schema": {},
                    "output_schema": {},
                }
            }
            super().__init__()

        def run_tool(self, tool_name: str, args: dict):
            pass

    with pytest.raises(ValueError, match="description"):
        BadPlugin()


def test_non_string_description_rejected():
    """Verify tool with non-string description is rejected."""

    class BadPlugin(BasePlugin):
        name = "bad"

        def __init__(self):
            self.tools = {
                "detect": {
                    "handler": lambda: None,
                    "description": 123,  # not a string
                    "input_schema": {},
                    "output_schema": {},
                }
            }
            super().__init__()

        def run_tool(self, tool_name: str, args: dict):
            pass

    with pytest.raises(ValueError, match="description"):
        BadPlugin()


def test_missing_input_schema_rejected():
    """Verify tool without input_schema is rejected."""

    class BadPlugin(BasePlugin):
        name = "bad"

        def __init__(self):
            self.tools = {
                "detect": {
                    "handler": lambda: None,
                    "description": "Detect",
                    # missing input_schema
                    "output_schema": {},
                }
            }
            super().__init__()

        def run_tool(self, tool_name: str, args: dict):
            pass

    with pytest.raises(ValueError, match="input_schema"):
        BadPlugin()


def test_non_dict_input_schema_rejected():
    """Verify tool with non-dict input_schema is rejected."""

    class BadPlugin(BasePlugin):
        name = "bad"

        def __init__(self):
            self.tools = {
                "detect": {
                    "handler": lambda: None,
                    "description": "Detect",
                    "input_schema": "not_a_dict",
                    "output_schema": {},
                }
            }
            super().__init__()

        def run_tool(self, tool_name: str, args: dict):
            pass

    with pytest.raises(ValueError, match="input_schema"):
        BadPlugin()


def test_missing_output_schema_rejected():
    """Verify tool without output_schema is rejected."""

    class BadPlugin(BasePlugin):
        name = "bad"

        def __init__(self):
            self.tools = {
                "detect": {
                    "handler": lambda: None,
                    "description": "Detect",
                    "input_schema": {},
                    # missing output_schema
                }
            }
            super().__init__()

        def run_tool(self, tool_name: str, args: dict):
            pass

    with pytest.raises(ValueError, match="output_schema"):
        BadPlugin()


def test_non_dict_output_schema_rejected():
    """Verify tool with non-dict output_schema is rejected."""

    class BadPlugin(BasePlugin):
        name = "bad"

        def __init__(self):
            self.tools = {
                "detect": {
                    "handler": lambda: None,
                    "description": "Detect",
                    "input_schema": {},
                    "output_schema": 123,
                }
            }
            super().__init__()

        def run_tool(self, tool_name: str, args: dict):
            pass

    with pytest.raises(ValueError, match="output_schema"):
        BadPlugin()


def test_tool_not_dict_rejected():
    """Verify tool value that is not a dict is rejected."""

    class BadPlugin(BasePlugin):
        name = "bad"

        def __init__(self):
            self.tools = {"detect": "not_a_dict"}  # tool value must be dict
            super().__init__()

        def run_tool(self, tool_name: str, args: dict):
            pass

    with pytest.raises(ValueError, match="must be a dict"):
        BadPlugin()
