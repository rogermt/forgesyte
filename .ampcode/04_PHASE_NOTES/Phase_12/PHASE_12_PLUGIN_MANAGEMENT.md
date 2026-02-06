# Phase 12 — Plugin Management Subsystem Code Bundle

Below are all coding files for the Phase 12 plugin management subsystem.

---

## server/app/services/plugin_management_service.py

```python
from typing import Any, Dict, List, Tuple

from app.plugins.runtime.tool_runner import ToolRunner
from app.plugins.loader.plugin_registry import get_registry


class PluginManagementService:
    """
    Phase 12: selects plugins and delegates execution to ToolRunner.
    No direct plugin.run() calls are allowed anywhere else.
    """

    def __init__(self) -> None:
        self._registry = get_registry()
        self._runner = ToolRunner()

    def list_plugins(self) -> List[str]:
        return list(self._registry._plugins.keys())

    def execute_plugin(
        self,
        plugin_name: str,
        payload: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Execute a single plugin via ToolRunner.
        """
        # Phase 12 invariant: NO direct plugin.run() here.
        return self._runner.run(plugin_name=plugin_name, payload=payload)
```

---

## server/tests/phase_12/test_toolrunner_called_for_all_plugins.py

```python
from app.services.plugin_management_service import PluginManagementService
from app.plugins.runtime.tool_runner import ToolRunner


def test_plugin_management_uses_toolrunner(monkeypatch):
    called = {}

    def fake_run(self, plugin_name, payload):
        called["plugin_name"] = plugin_name
        called["payload"] = payload
        return {"ok": True}, {}

    monkeypatch.setattr(ToolRunner, "run", fake_run)

    svc = PluginManagementService()
    result, error = svc.execute_plugin(
        plugin_name="fake_plugin",
        payload={"image": b"123", "mime_type": "image/png"},
    )

    assert result == {"ok": True}
    assert error == {}
    assert called["plugin_name"] == "fake_plugin"
    assert called["payload"]["image"] == b"123"
```

---

## server/tests/phase_12/test_no_direct_plugin_run_calls.py

```python
import inspect
import app.services.plugin_management_service as pms


def test_no_direct_plugin_run_calls_in_plugin_management():
    source = inspect.getsource(pms.PluginManagementService)
    # Phase 12 invariant: plugin.run( must not appear in this class.
    assert "plugin.run(" not in source
```

---

# End of Plugin Management subsystem bundle
