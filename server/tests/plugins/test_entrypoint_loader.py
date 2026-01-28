"""TDD tests for entry-point plugin loader."""

from app.plugin_loader import PluginRegistry
from app.plugins.base import BasePlugin


def test_loader_rejects_non_baseplugin(monkeypatch):
    """Entry-point loader must reject plugins that don't subclass BasePlugin."""

    class NotAPlugin:
        name = "bad"
        tools = {}

    def fake_eps(group):
        if group != "forgesyte.plugins":
            return []

        class EP:
            name = "bad"

            def load(self):
                return NotAPlugin

        return [EP()]

    monkeypatch.setattr("app.plugin_loader.entry_points", fake_eps)

    registry = PluginRegistry()
    result = registry.load_plugins()

    assert "bad" in result["errors"]
    assert "bad" not in result["loaded"]


def test_loader_accepts_valid_plugin(monkeypatch):
    """Entry-point loader must accept valid BasePlugin subclasses."""

    class GoodPlugin(BasePlugin):
        name = "good"

        def __init__(self):
            self.tools = {"echo": lambda x: x}
            super().__init__()

        def run_tool(self, tool_name, args):
            return self.tools[tool_name](**args)

    def fake_eps(group):
        if group != "forgesyte.plugins":
            return []

        class EP:
            name = "good"

            def load(self):
                return GoodPlugin

        return [EP()]

    monkeypatch.setattr("app.plugin_loader.entry_points", fake_eps)

    registry = PluginRegistry()
    result = registry.load_plugins()

    assert "good" in result["loaded"]
    assert result["loaded"]["good"] == "entrypoint:good"
    assert registry.get("good") is not None
    assert isinstance(registry.get("good"), BasePlugin)


def test_duplicate_plugin_names_rejected(monkeypatch):
    """Entry-point loader must reject duplicate plugin names."""

    class P1(BasePlugin):
        name = "dup"

        def __init__(self):
            self.tools = {}
            super().__init__()

        def run_tool(self, t, a):
            return None

    class P2(BasePlugin):
        name = "dup"

        def __init__(self):
            self.tools = {}
            super().__init__()

        def run_tool(self, t, a):
            return None

    def fake_eps(group):
        if group != "forgesyte.plugins":
            return []

        class EP1:
            name = "p1"

            def load(self):
                return P1

        class EP2:
            name = "p2"

            def load(self):
                return P2

        return [EP1(), EP2()]

    monkeypatch.setattr("app.plugin_loader.entry_points", fake_eps)

    registry = PluginRegistry()
    result = registry.load_plugins()

    # Only first should succeed, second should error
    assert "dup" in result["loaded"]
    assert "p2" in result["errors"]
    assert "Duplicate" in result["errors"]["p2"]


def test_validation_hook_called(monkeypatch):
    """Entry-point loader must call optional validate() hook."""

    validation_calls = []

    class ValidatingPlugin(BasePlugin):
        name = "validating"

        def __init__(self):
            self.tools = {}
            super().__init__()

        def run_tool(self, t, a):
            return None

        def validate(self):
            validation_calls.append(self.name)

    def fake_eps(group):
        if group != "forgesyte.plugins":
            return []

        class EP:
            name = "validating"

            def load(self):
                return ValidatingPlugin

        return [EP()]

    monkeypatch.setattr("app.plugin_loader.entry_points", fake_eps)

    registry = PluginRegistry()
    result = registry.load_plugins()

    assert "validating" in result["loaded"]
    assert "validating" in validation_calls


def test_validation_failure_prevents_loading(monkeypatch):
    """Entry-point loader must prevent plugin load if validate() fails."""

    class BadValidationPlugin(BasePlugin):
        name = "bad_validate"

        def __init__(self):
            self.tools = {}
            super().__init__()

        def run_tool(self, t, a):
            return None

        def validate(self):
            raise RuntimeError("Validation failed")

    def fake_eps(group):
        if group != "forgesyte.plugins":
            return []

        class EP:
            name = "bad_validate"

            def load(self):
                return BadValidationPlugin

        return [EP()]

    monkeypatch.setattr("app.plugin_loader.entry_points", fake_eps)

    registry = PluginRegistry()
    result = registry.load_plugins()

    assert "bad_validate" not in result["loaded"]
    assert "bad_validate" in result["errors"]
    assert "Validation failed" in result["errors"]["bad_validate"]


def test_partial_loading_on_mixed_plugins(monkeypatch):
    """Entry-point loader must load valid plugins even if others fail."""

    class ValidPlugin(BasePlugin):
        name = "valid"

        def __init__(self):
            self.tools = {}
            super().__init__()

        def run_tool(self, t, a):
            return None

    class InvalidPlugin:
        name = "invalid"

    def fake_eps(group):
        if group != "forgesyte.plugins":
            return []

        class EP1:
            name = "valid_ep"

            def load(self):
                return ValidPlugin

        class EP2:
            name = "invalid_ep"

            def load(self):
                return InvalidPlugin

        return [EP1(), EP2()]

    monkeypatch.setattr("app.plugin_loader.entry_points", fake_eps)

    registry = PluginRegistry()
    result = registry.load_plugins()

    assert "valid" in result["loaded"]
    assert "invalid_ep" in result["errors"]
    assert registry.get("valid") is not None


def test_list_returns_all_plugins(monkeypatch):
    """PluginRegistry.list() must return all loaded plugins."""

    class P1(BasePlugin):
        name = "p1"

        def __init__(self):
            self.tools = {}
            super().__init__()

        def run_tool(self, t, a):
            return None

    class P2(BasePlugin):
        name = "p2"

        def __init__(self):
            self.tools = {}
            super().__init__()

        def run_tool(self, t, a):
            return None

    def fake_eps(group):
        if group != "forgesyte.plugins":
            return []

        class EP1:
            name = "p1_ep"

            def load(self):
                return P1

        class EP2:
            name = "p2_ep"

            def load(self):
                return P2

        return [EP1(), EP2()]

    monkeypatch.setattr("app.plugin_loader.entry_points", fake_eps)

    registry = PluginRegistry()
    registry.load_plugins()

    plugins = registry.list()
    assert len(plugins) == 2
    assert "p1" in plugins
    assert "p2" in plugins
    assert all(isinstance(p, BasePlugin) for p in plugins.values())


def test_no_plugins_available(monkeypatch):
    """Entry-point loader must handle case when no plugins are available."""

    def fake_eps(group):
        return []

    monkeypatch.setattr("app.plugin_loader.entry_points", fake_eps)

    registry = PluginRegistry()
    result = registry.load_plugins()

    assert result["loaded"] == {}
    assert result["errors"] == {}
    assert registry.list() == {}
