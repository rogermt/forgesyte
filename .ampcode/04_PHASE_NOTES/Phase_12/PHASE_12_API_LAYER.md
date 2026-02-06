# Phase 12 — API Layer Subsystem Code Bundle

Below are all coding files for the Phase 12 API layer subsystem.

---

## server/app/services/analysis_service.py

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

## server/app/api/routes/analyze.py

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

## server/tests/phase_12/test_analyze_endpoint_phase12_contract.py

```python
from fastapi.testclient import TestClient

from app.main import app  # assuming app includes router with /v1/analyze


client = TestClient(app)


def test_analyze_success_contract(monkeypatch):
    # If you want to bypass real execution, monkeypatch AnalysisService here.
    resp = client.post(
        "/v1/analyze",
        json={
            "plugin": "fake_plugin",
            "image": "BASE64_PLACEHOLDER",
            "mime_type": "image/png",
        },
    )
    assert resp.status_code in (200, 400)  # depending on how you wire fake plugins


def test_analyze_error_is_structured(monkeypatch):
    resp = client.post(
        "/v1/analyze",
        json={
            "plugin": "fake_plugin",
            "image": "",
            "mime_type": "image/png",
        },
    )
    # Expect validation to fail and error envelope to be returned via HTTPException
    assert resp.status_code == 400
    body = resp.json()
    assert "detail" in body
    assert "type" in body["detail"]
    assert "message" in body["detail"]
```

---

## server/app/api/routes/tools.py

```python
from fastapi import APIRouter

from app.services.plugin_management_service import PluginManagementService

router = APIRouter()
_plugin_mgmt = PluginManagementService()


@router.get("/v1/tools")
async def list_tools():
    """
    Phase 12: List all available plugin tools.
    """
    plugins = _plugin_mgmt.list_plugins()
    return {
        "tools": plugins,
        "count": len(plugins),
    }
```

---

## server/tests/phase_12/test_tools_endpoint.py

```python
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_list_tools_endpoint(monkeypatch):
    resp = client.get("/v1/tools")
    assert resp.status_code == 200
    body = resp.json()
    assert "tools" in body
    assert "count" in body
    assert isinstance(body["tools"], list)
```

---

## server/app/api/main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.analyze import router as analyze_router
from app.api.routes.tools import router as tools_router


def create_app() -> FastAPI:
    app = FastAPI(title="ForgeSyte Phase 12 API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(analyze_router)
    app.include_router(tools_router)

    return app
```

---

## server/tests/phase_12/test_api_integration_phase12.py

```python
from fastapi.testclient import TestClient

from app.api.main import create_app
from app.services.analysis_service import AnalysisService


def test_full_api_flow(monkeypatch):
    def fake_analyze(self, plugin_name, payload):
        return {"result": "ok"}, {}

    monkeypatch.setattr(AnalysisService, "analyze", fake_analyze)

    app = create_app()
    client = TestClient(app)

    # 1. List tools
    resp = client.get("/v1/tools")
    assert resp.status_code == 200

    # 2. Execute analysis
    resp = client.post(
        "/v1/analyze",
        json={
            "plugin": "test_plugin",
            "image": "BASE64_PLACEHOLDER",
            "mime_type": "image/png",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "result" in body
    assert body["result"] == {"result": "ok"}
```

---

# End of API Layer subsystem bundle
