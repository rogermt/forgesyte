# Phase 12 — Error Handling Subsystem Code Bundle

Below are all coding files for the Phase 12 error-handling subsystem.

---

## server/app/phase12/error_envelope.py

```python
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import traceback


def _classify_error(exc: Exception) -> str:
    """
    Phase 12: classify exceptions into structured error types.
    """
    name = exc.__class__.__name__
    if "Validation" in name:
        return "ValidationError"
    if "Plugin" in name:
        return "PluginError"
    return "ExecutionError"


def build_error_envelope(exc: Exception, plugin_name: Optional[str]) -> Dict[str, Any]:
    """
    Build a structured error envelope for all exceptions.
    """
    error_type = _classify_error(exc)
    message = str(exc) or error_type

    tb = traceback.format_exc()

    return {
        "error": {
            "type": error_type,
            "message": message,
            "details": {},
            "plugin": plugin_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "_internal": {
            "traceback": tb,
        },
    }
```

---

## server/tests/phase_12/test_error_envelope_structure.py

```python
from app.phase12.error_envelope import build_error_envelope


def test_error_envelope_structure():
    class FakeError(Exception):
        pass

    err = FakeError("boom")
    env = build_error_envelope(err, plugin_name="fake")

    assert "error" in env
    assert env["error"]["type"] == "ExecutionError"
    assert env["error"]["message"] == "boom"
    assert env["error"]["plugin"] == "fake"
    assert "timestamp" in env["error"]
    assert "_internal" in env
    assert "traceback" in env["_internal"]
```

---

## server/tests/phase_12/test_unstructured_errors_fail.py

```python
from app.plugins.runtime.tool_runner import ToolRunner
from app.plugins.loader.plugin_registry import get_registry


class _ExplodingPlugin:
    def run(self, payload):
        raise RuntimeError("kaboom")


def test_unstructured_errors_fail(monkeypatch):
    def fake_get_plugin(name: str):
        return _ExplodingPlugin()

    reg = get_registry()
    monkeypatch.setattr(reg, "get_plugin", fake_get_plugin)

    runner = ToolRunner()
    result, error = runner.run(
        plugin_name="whatever",
        payload={"image": b"123", "mime_type": "image/png"},
    )

    assert result == {}
    assert "error" in error
    assert "error" in error
    assert error["error"]["type"] == "ExecutionError"
    assert error["error"]["message"] == "kaboom"
```

---

# End of Error Handling subsystem bundle
