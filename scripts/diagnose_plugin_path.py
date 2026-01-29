"""
diagnose_plugin_path.py

Modern, future-proof diagnostic tool for ForgeSyte plugin discovery.
Uses importlib.metadata instead of deprecated pkg_resources.
"""

import importlib
from importlib.metadata import entry_points
import sys


def diagnose_plugin_paths(entrypoint_group="forgesyte.plugins"):
    print("\n=== ForgeSyte Plugin Path Diagnostic ===\n")

    # Python 3.10+ supports entry_points(group=...)
    if sys.version_info >= (3, 10):
        eps = entry_points(group=entrypoint_group)
    else:
        eps = entry_points().get(entrypoint_group, [])

    if not eps:
        print(f"No entrypoints found for group '{entrypoint_group}'.")
        print("\n=== End Diagnostic ===\n")
        return

    for ep in eps:
        print(f"Discovered plugin entrypoint: {ep.name}")
        print(f"  Module path: {ep.module}")
        print(f"  Object name: {ep.attr}")

        try:
            plugin_class = ep.load()
            module = importlib.import_module(plugin_class.__module__)
            print(f"  Loaded plugin class: {plugin_class.__name__}")
            print(f"  Loaded from file: {module.__file__}")
        except Exception as e:
            print(f"  ERROR loading plugin: {e}")

        print()

    print("=== End Diagnostic ===\n")


if __name__ == "__main__":
    diagnose_plugin_paths()
