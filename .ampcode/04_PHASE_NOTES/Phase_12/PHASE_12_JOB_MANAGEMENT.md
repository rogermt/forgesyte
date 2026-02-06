# Phase 12 — Job Management Subsystem Code Bundle

Below are all coding files for the Phase 12 job management subsystem.

---

## server/app/services/job_management_service.py

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

## server/tests/phase_12/test_job_management_uses_plugin_management.py

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

---

## server/tests/phase_12/test_job_status_transitions.py

```python
from app.services.job_management_service import JobManagementService
from app.services.plugin_management_service import PluginManagementService


def test_job_status_transitions_on_success(monkeypatch):
    def fake_execute(self, plugin_name, payload):
        return {"result": "ok"}, {}

    monkeypatch.setattr(PluginManagementService, "execute_plugin", fake_execute)

    svc = JobManagementService()
    job_id = svc.create_job(
        plugin_name="fake_plugin",
        payload={"image": b"123", "mime_type": "image/png"},
    )

    job = svc.get_job(job_id)
    assert job["status"] == "PENDING"

    svc.run_job(job_id)

    job = svc.get_job(job_id)
    assert job["status"] == "SUCCESS"
    assert job["result"] == {"result": "ok"}
    assert job["error"] is None
```

---

## server/tests/phase_12/test_job_status_transitions_on_error.py

```python
from app.services.job_management_service import JobManagementService
from app.services.plugin_management_service import PluginManagementService


def test_job_status_transitions_on_error(monkeypatch):
    def fake_execute(self, plugin_name, payload):
        return {}, {
            "error": {
                "type": "ExecutionError",
                "message": "plugin failed",
                "plugin": "fake_plugin",
            }
        }

    monkeypatch.setattr(PluginManagementService, "execute_plugin", fake_execute)

    svc = JobManagementService()
    job_id = svc.create_job(
        plugin_name="fake_plugin",
        payload={"image": b"123", "mime_type": "image/png"},
    )

    result, error = svc.run_job(job_id)

    assert result == {}
    assert "error" in error

    job = svc.get_job(job_id)
    assert job["status"] == "FAILED"
    assert job["error"]["error"]["type"] == "ExecutionError"
    assert job["result"] is None
```

---

# End of Job Management subsystem bundle
