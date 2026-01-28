import importlib
import inspect
import pkgutil

from app import plugins as plugins
from app.plugin_loader import PluginRegistry
from app.plugins.base import BasePlugin


def test_no_duplicate_baseplugin_definitions():
    """
    Regression test:
    Ensures there is exactly ONE BasePlugin class in the entire codebase.

    This prevents the catastrophic bug where plugin_loader.py
    accidentally defined its own BasePlugin, causing isinstance()
    checks to fail due to type identity mismatch.
    """

    baseplugin_classes = []

    # Walk all modules under app.plugins.*
    for module_info in pkgutil.walk_packages(plugins.__path__, plugins.__name__ + "."):
        module = importlib.import_module(module_info.name)

        # Inspect all classes in the module
        for _, obj in inspect.getmembers(module, inspect.isclass):
            # Look for classes named BasePlugin
            if obj.__name__ == "BasePlugin":
                baseplugin_classes.append(obj)

    # There must be exactly one BasePlugin class
    found = len(baseplugin_classes)
    expected_msg = (
        f"Expected exactly 1 BasePlugin class, found {found}: {baseplugin_classes}"
    )
    assert len(baseplugin_classes) == 1, expected_msg

    # And it must be the canonical one
    assert baseplugin_classes[0] is BasePlugin, (
        "The BasePlugin found in the codebase is not the canonical BasePlugin "
        "imported from app.plugins.base"
    )


def test_registry_uses_canonical_baseplugin():
    """
    Ensures PluginRegistry enforces the canonical BasePlugin identity.
    """

    class GoodPlugin(BasePlugin):
        name = "good"

        def __init__(self):
            self.tools = {"echo": lambda x: x}
            super().__init__()

        def run_tool(self, tool_name, args):
            return self.tools[tool_name](**args)

    registry = PluginRegistry()
    registry.register(GoodPlugin())  # must not raise
