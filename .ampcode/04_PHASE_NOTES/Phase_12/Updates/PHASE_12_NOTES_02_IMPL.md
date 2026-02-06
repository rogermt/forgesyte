Here we go, Roger — full Phase 12 implementation, wired and Phase‑11‑safe, with **file paths + full code**.

---

### `server/app/plugins/loader/plugin_registry.py`

```python
from typing import Any, Dict, List, Optional
from datetime import datetime


class PluginRegistry:
    """
    Phase 11 + Phase 12:
    - Phase 11: plugin registration and lookup
    - Phase 12: execution metrics and lifecycle state
    """

    def __init__(self) -> None:
        self._plugins: Dict[str, Any] = {}
        self._status: Dict[str, Dict[str, Any]] = {}

    # ---------- PHASE 11 BEHAVIOUR (UNCHANGED) ----------

    def register(self, name: str, plugin: Any) -> None:
        self._plugins[name] = plugin
        if name not in self._status:
            self._status[name] = {
                "success_count": 0,
                "error_count": 0,
                "last_execution_time_ms": None,
                "avg_execution_time_ms": None,
                "last_used": None,
                "state": "IDLE",
            }

    def get_plugin(self, name: str) -> Any:
        return self._plugins[name]

    def list_plugins(self) -> List[str]:
        return list(self._plugins.keys())

    # ---------- PHASE 12 ADDITIVE BEHAVIOUR ----------

    def update_execution_metrics(
        self,
        plugin_name: str,
        state: str,
        elapsed_ms: int,
        had_error: bool,
    ) -> None:
        """
        Phase 12: update metrics and lifecycle state after each execution.
        """
        if plugin_name not in self._status:
            # Ensure status exists even if plugin was registered earlier without metrics.
            self._status[plugin_name] = {
                "success_count": 0,
                "error_count": 0,
                "last_execution_time_ms": None,
                "avg_execution_time_ms": None,
                "last_used": None,
                "state": "IDLE",
            }

        status = self._status[plugin_name]

        if had_error:
            status["error_count"] += 1
        else:
            status["success_count"] += 1

        status["last_execution_time_ms"] = elapsed_ms

        if status["avg_execution_time_ms"] is None:
            status["avg_execution_time_ms"] = elapsed_ms
        else:
            status["avg_execution_time_ms"] = int(
                (status["avg_execution_time_ms"] + elapsed_ms) / 2
            )

        status["last_used"] = datetime.utcnow().isoformat()
        status["state"] = state

    def get_status(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        return self._status.get(plugin_name)

    def all_status(self) -> List[Dict[str, Any]]:
        return list(self._status.values())


_registry = PluginRegistry()


def get_registry() -> PluginRegistry:
    return _registry
```

---

### `server/app/phase12/validation.py`

```python
from typing import Any, Dict


class InputValidationError(Exception):
    """Raised when incoming request payload is invalid."""
    pass


class OutputValidationError(Exception):
    """Raised when plugin output is invalid or malformed."""
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

### `server/app/phase12/error_envelope.py`

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

### `server/app/plugins/runtime/tool_runner.py`

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

### `server/app/services/plugin_management_service.py`

```python
from typing import Any, Dict, List, Tuple

from app.plugins.runtime.tool_runner import ToolRunner
from app.plugins.loader.plugin_registry import get_registry


class PluginManagementService:
    """
    Phase 12: selects plugins and delegates execution to ToolRunner.
    No direct plugin.run() calls are allowed here.
    """

    def __init__(self) -> None:
        self._registry = get_registry()
        self._runner = ToolRunner()

    def list_plugins(self) -> List[str]:
        return self._registry.list_plugins()

    def execute_plugin(
        self,
        plugin_name: str,
        payload: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Execute a single plugin via ToolRunner.
        """
        return self._runner.run(plugin_name=plugin_name, payload=payload)
```

---

### `server/app/services/job_management_service.py`

```python
from typing import Any, Dict, Tuple
from uuid import uuid4

from app.services.plugin_management_service import PluginManagementService


class JobManagementService:
    """
    Phase 12: owns job records and delegates execution to PluginManagementService.
    It does NOT call ToolRunner or plugin.run() directly.
    """

    def __init__(self) -> None:
        self._plugin_mgmt = PluginManagementService()
        self._jobs: Dict[str, Dict[str, Any]] = {}

    def create_job(self, plugin_name: str, payload: Dict[str, Any]) -> str:
        job_id = str(uuid4())
        self._jobs[job_id] = {
            "id": job_id,
            "plugin": plugin_name,
            "payload": payload,
            "status": "PENDING",
            "result": None,
            "error": None,
        }
        return job_id

    def run_job(self, job_id: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        job = self._jobs[job_id]
        job["status"] = "RUNNING"

        result, error = self._plugin_mgmt.execute_plugin(
            plugin_name=job["plugin"],
            payload=job["payload"],
        )

        if error:
            job["status"] = "FAILED"
            job["error"] = error
        else:
            job["status"] = "SUCCESS"
            job["result"] = result

        return result, error

    def get_job(self, job_id: str) -> Dict[str, Any]:
        return self._jobs[job_id]
```

---

### `server/app/services/analysis_service.py`

```python
from typing import Any, Dict, Tuple

from app.services.job_management_service import JobManagementService


class AnalysisService:
    """
    Phase 12: API-facing service that validates high-level request shape
    and delegates to JobManagementService.
    """

    def __init__(self) -> None:
        self._jobs = JobManagementService()

    def analyze(self, plugin_name: str, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        job_id = self._jobs.create_job(plugin_name=plugin_name, payload=payload)
        result, error = self._jobs.run_job(job_id)
        return result, error
```

---

### `server/app/api/routes/analyze.py`

```python
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.services.analysis_service import AnalysisService

router = APIRouter()
_service = AnalysisService()


@router.post("/v1/analyze")
async def analyze(payload: Dict[str, Any]):
    """
    Phase 12: API endpoint that returns structured success or structured error.
    """
    plugin_name = payload.get("plugin", "default")
    result, error = _service.analyze(plugin_name=plugin_name, payload=payload)

    if error:
        # Phase 12: structured error envelope only.
        raise HTTPException(status_code=400, detail=error["error"])

    return {
        "result": result,
        "plugin": plugin_name,
    }
```

---

### `server/tests/phase_12/test_toolrunner_happy_path.py`

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

### `server/tests/phase_12/test_input_validation.py`

```python
import pytest
from app.phase12.validation import (
    validate_input_payload,
    InputValidationError,
)


def test_input_validation_rejects_empty_image():
    with pytest.raises(InputValidationError):
        validate_input_payload({"image": b"", "mime_type": "image/png"})


def test_input_validation_rejects_missing_mime():
    with pytest.raises(InputValidationError):
        validate_input_payload({"image": b"123"})


def test_input_validation_accepts_valid_payload():
    validate_input_payload({"image": b"123", "mime_type": "image/png"})
```

---

### `server/tests/phase_12/test_output_validation.py`

```python
import pytest
from app.phase12.validation import (
    validate_plugin_output,
    OutputValidationError,
)


def test_output_validation_rejects_none():
    with pytest.raises(OutputValidationError):
        validate_plugin_output(None)


def test_output_validation_rejects_non_dict():
    with pytest.raises(OutputValidationError):
        validate_plugin_output("not a dict")


def test_output_validation_accepts_valid_dict():
    assert validate_plugin_output({"ok": True}) == {"ok": True}
```

---

### `server/tests/phase_12/test_error_envelope_structure.py`

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

### `server/tests/phase_12/test_unstructured_errors_fail.py`

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
    assert error["error"]["type"] == "ExecutionError"
    assert error["error"]["message"] == "kaboom"
```

---

### `server/tests/phase_12/test_toolrunner_called_for_all_plugins.py`

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

### `server/tests/phase_12/test_job_management_uses_plugin_management.py`

```python
from app.services.job_management_service import JobManagementService
from app.services.plugin_management_service import PluginManagementService


def test_job_management_delegates_to_plugin_management(monkeypatch):
    called = {}

    def fake_execute(self, plugin_name, payload):
        called["plugin_name"] = plugin_name
        called["payload"] = payload
        return {"ok": True}, {}

    monkeypatch.setattr(PluginManagementService, "execute_plugin", fake_execute)

    svc = JobManagementService()
    job_id = svc.create_job(
        plugin_name="fake_plugin",
        payload={"image": b"123", "mime_type": "image/png"},
    )

    result, error = svc.run_job(job_id)

    assert result == {"ok": True}
    assert error == {}
    assert called["plugin_name"] == "fake_plugin"
    assert called["payload"]["image"] == b"123"

    job = svc.get_job(job_id)
    assert job["status"] == "SUCCESS"
    assert job["result"] == {"ok": True}
```

