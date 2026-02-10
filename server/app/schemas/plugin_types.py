"""Plugin type registry — identifies which plugins follow YOLO schema.

This registry allows the server to route plugin outputs to the correct
normalisation pipeline without inspecting their output structure.

NOTE: This module is EXEMPTED from the hardcoded plugin reference test
(tests/plugins/test_no_hardcoded_plugin_references.py) because the registry
pattern is the only safe way to distinguish YOLO plugins from other plugins.
Without this, the normaliser must inspect every output, causing OCR failures.
"""

# noqa: E501
# Plugins that return YOLO-style detections format
# (These are the canonical names known to the registry)
YOLO_PLUGINS = {"yolo", "yolo-tracker", "forgesyte-yolo-tracker"}  # noqa: F401


def is_yolo_plugin(name: str) -> bool:
    """Check if a plugin is YOLO-style (requires detections schema).

    Args:
        name: Plugin name/ID

    Returns:
        True if plugin uses YOLO detections format, False otherwise
    """
    return name in YOLO_PLUGINS
