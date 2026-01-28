"""Tests for schema validation in PluginRegistry."""

import pytest

from app.plugin_loader import PluginRegistry
from app.plugins.base import BasePlugin


def test_valid_schema_loads():
    """Verify plugin with valid tool schemas loads via registry."""

    class GoodPlugin(BasePlugin):
        name = "good"

        def __init__(self):
            self.tools = {
                "detect": {
                    "handler": self.detect,
                    "description": "Detect objects",
                    "input_schema": {"frame_base64": {"type": "string"}},
                    "output_schema": {"detections": {"type": "array"}},
                }
            }
            super().__init__()

        def detect(self, frame_base64: str):
            return {"detections": []}

        def run_tool(self, tool_name: str, args: dict):
            meta = self.tools[tool_name]
            return meta["handler"](**args)

    registry = PluginRegistry()
    registry.register(GoodPlugin())
    assert registry.get("good") is not None


def test_missing_description_rejected_by_registry():
    """Verify registry rejects tool without description (caught in BasePlugin)."""

    class BadPlugin(BasePlugin):
        name = "bad"

        def __init__(self):
            self.tools = {
                "detect": {
                    "handler": self.detect,
                    # missing description
                    "input_schema": {},
                    "output_schema": {},
                }
            }
            super().__init__()

        def detect(self):
            return {}

        def run_tool(self, tool_name: str, args: dict):
            pass

    # Error occurs during BasePlugin init, not registry
    with pytest.raises(ValueError, match="description"):
        BadPlugin()


def test_non_dict_schema_rejected_by_registry():
    """Verify registry rejects tool with non-dict schemas (caught in BasePlugin)."""

    class BadPlugin(BasePlugin):
        name = "bad"

        def __init__(self):
            self.tools = {
                "detect": {
                    "handler": self.detect,
                    "description": "x",
                    "input_schema": None,
                    "output_schema": 123,
                }
            }
            super().__init__()

        def detect(self):
            return {}

        def run_tool(self, tool_name: str, args: dict):
            pass

    # Error occurs during BasePlugin init, not registry
    with pytest.raises(ValueError, match="input_schema"):
        BadPlugin()


def test_schema_must_be_json_serializable():
    """Verify registry rejects tool with non-serializable schema."""

    class BadPlugin(BasePlugin):
        name = "bad"

        def __init__(self):
            self.tools = {
                "detect": {
                    "handler": self.detect,
                    "description": "x",
                    "input_schema": {"bad": {1, 2}},  # set is not JSON serializable
                    "output_schema": {},
                }
            }
            super().__init__()

        def detect(self):
            return {}

        def run_tool(self, tool_name: str, args: dict):
            pass

    registry = PluginRegistry()
    with pytest.raises(ValueError, match="JSON-serializable"):
        registry.register(BadPlugin())


def test_missing_input_schema_rejected_by_registry():
    """Verify registry rejects tool without input_schema (caught in BasePlugin)."""

    class BadPlugin(BasePlugin):
        name = "bad"

        def __init__(self):
            self.tools = {
                "detect": {
                    "handler": self.detect,
                    "description": "x",
                    # missing input_schema
                    "output_schema": {},
                }
            }
            super().__init__()

        def detect(self):
            return {}

        def run_tool(self, tool_name: str, args: dict):
            pass

    # Error occurs during BasePlugin init, not registry
    with pytest.raises(ValueError, match="input_schema"):
        BadPlugin()


def test_missing_output_schema_rejected_by_registry():
    """Verify registry rejects tool without output_schema (caught in BasePlugin)."""

    class BadPlugin(BasePlugin):
        name = "bad"

        def __init__(self):
            self.tools = {
                "detect": {
                    "handler": self.detect,
                    "description": "x",
                    "input_schema": {},
                    # missing output_schema
                }
            }
            super().__init__()

        def detect(self):
            return {}

        def run_tool(self, tool_name: str, args: dict):
            pass

    # Error occurs during BasePlugin init, not registry
    with pytest.raises(ValueError, match="output_schema"):
        BadPlugin()
