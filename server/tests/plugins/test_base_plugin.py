import pytest

from app.plugins.base import BasePlugin


def test_valid_plugin_loads():
    class GoodPlugin(BasePlugin):
        name = "good"

        def echo_handler(self, **args):
            return args

        def __init__(self):
            self.tools = {
                "echo": {
                    "description": "Echo tool",
                    "input_schema": {"type": "object", "properties": {}},
                    "output_schema": {"type": "object"},
                    "handler": self.echo_handler,
                }
            }
            super().__init__()

        def run_tool(self, tool_name, args):
            if tool_name == "echo":
                return args

    plugin = GoodPlugin()
    assert plugin.name == "good"
    assert isinstance(plugin.tools["echo"], dict)


def test_missing_name_raises():
    class BadPlugin(BasePlugin):
        def __init__(self):
            self.tools = {}
            super().__init__()

        def run_tool(self, tool_name, args):
            return None

    with pytest.raises(ValueError):
        BadPlugin()


def test_missing_tools_raises():
    class BadPlugin(BasePlugin):
        name = "bad"

        def __init__(self):
            # tools missing
            super().__init__()

        def run_tool(self, tool_name, args):
            return None

    with pytest.raises(ValueError):
        BadPlugin()


def test_non_callable_tool_raises():
    class BadPlugin(BasePlugin):
        name = "bad"

        def __init__(self):
            self.tools = {"not_dict": 123}
            super().__init__()

        def run_tool(self, tool_name, args):
            return None

    with pytest.raises(ValueError):
        BadPlugin()


def test_run_tool_is_abstract():
    class IncompletePlugin(BasePlugin):
        name = "incomplete"

        def __init__(self):
            self.tools = {}
            super().__init__()

    with pytest.raises(TypeError):
        IncompletePlugin()
