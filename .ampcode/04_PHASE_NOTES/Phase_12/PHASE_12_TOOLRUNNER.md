# Phase 12 — ToolRunner Subsystem Code Bundle

Below are all coding files for the ToolRunner subsystem.

---

## server/app/plugins/runtime/tool_runner.py

```python
import time
from typing import Any, Dict, Tuple

from app.plugins.loader.plugin_registry import get_registry
from app.phase12.error_envelope import build_error_envelope
from app.phase12.validation import validate_input_payload, validate_plugin_output


class ToolRunner:
    """
    Phase 12: single, governed execution path for all plugins.
    """

    def __init__(self) -> None:
        self._registry = get_registry()

    def run(self, plugin_name: str, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Execute a plugin in a governed way.

        Returns:
            (result, error) where exactly one is non-empty.
        """
        validate_input_payload(payload)

        plugin = self._registry.get_plugin(plugin_name)

        start = time.monotonic()
        error: Dict[str, Any] = {}
        result: Dict[str, Any] = {}

        try:
            raw_output = plugin.run(payload)
            result = validate_plugin_output(raw_output)
            final_state = "SUCCESS"
        except Exception as exc:  # noqa: BLE001
            error = build_error_envelope(exc, plugin_name=plugin_name)
            result = {}
            final_state = "ERROR"
        finally:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            self._registry.update_execution_metrics(
                plugin_name=plugin_name,
                state=final_state,
                elapsed_ms=elapsed_ms,
                had_error=bool(error),
            )

        return result, error
```

---

## server/app/phase12/error_envelope.py

```python
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import traceback


def _classify_error(exc: Exception) -> str:
    name = exc.__class__.__name__
    if "Validation" in name:
        return "ValidationError"
    if "Plugin" in name:
        return "PluginError"
    return "ExecutionError"


def build_error_envelope(exc: Exception, plugin_name: Optional[str]) -> Dict[str, Any]:
    """
    Phase 12: all errors must be structured.
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

## server/app/phase12/validation.py

```python
from typing import Any, Dict


class InputValidationError(Exception):
    pass


class OutputValidationError(Exception):
    pass


def validate_input_payload(payload: Dict[str, Any]) -> None:
    """
    Phase 12: input MUST be validated before execution.
    """
    image = payload.get("image")
    if not image:
        raise InputValidationError("Empty image payload")

    mime = payload.get("mime_type")
    if not mime or not isinstance(mime, str):
        raise InputValidationError("Missing or invalid mime_type")


def validate_plugin_output(raw_output: Any) -> Dict[str, Any]:
    """
    Phase 12: plugin output MUST be a dict-like structure.
    """
    if raw_output is None:
        raise OutputValidationError("Plugin returned None")

    if not isinstance(raw_output, dict):
        raise OutputValidationError("Plugin output must be a dict")

    return raw_output
```

---

## server/tests/phase_12/test_toolrunner_happy_path.py

```python
from app.plugins.runtime.tool_runner import ToolRunner
from app.plugins.loader.plugin_registry import get_registry


class _FakePlugin:
    def __init__(self) -> None:
        self.called = False

    def run(self, payload):
        self.called = True
        return {"ok": True}


def test_toolrunner_happy_path(monkeypatch):
    fake = _FakePlugin()

    def fake_get_plugin(name: str):
        assert name == "fake_plugin"
        return fake

    reg = get_registry()
    monkeypatch.setattr(reg, "get_plugin", fake_get_plugin)

    runner = ToolRunner()
    result, error = runner.run(
        plugin_name="fake_plugin",
        payload={"image": b"123", "mime_type": "image/png"},
    )

    assert fake.called is True
    assert result == {"ok": True}
    assert error == {}
```

---

# End of ToolRunner subsystem bundle
