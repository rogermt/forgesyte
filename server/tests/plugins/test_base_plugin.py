import pytest

from app.plugins.base import BasePlugin


def test_valid_plugin_loads():
    class GoodPlugin(BasePlugin):
        name = "good"

        def __init__(self):
            self.tools = {"echo": lambda x: x}
            super().__init__()

        def run_tool(self, tool_name, args):
            return self.tools[tool_name](**args)

    plugin = GoodPlugin()
    assert plugin.name == "good"
    assert callable(plugin.tools["echo"])


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
            self.tools = {"not_callable": 123}
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
