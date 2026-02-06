Roger, these are *excellent* final‑stage questions — the kind you ask when you’re about to lock Phase 12 into a real production codebase. Let’s go subsystem by subsystem and answer them **based on your actual architecture**, not hypotheticals.

I’ll be direct, decisive, and opinionated — because you need clarity, not ambiguity.

---

# ⭐ 1. **Existing Services Have Different Purposes**  
### *Should Phase 12 create NEW services or extend existing ones?*

### ✅ **Create NEW services. Do NOT extend the existing ones.**

Here’s why:

### Your current services have **established, Phase‑11‑stable responsibilities**:

| Existing Service | Current Purpose | Should Phase 12 modify it? |
|------------------|----------------|----------------------------|
| `PluginManagementService` | plugin metadata, reload, discovery | ❌ No — do NOT overload it with execution |
| `JobManagementService` | job persistence, DB queries | ❌ No — do NOT add execution logic |
| `AnalysisService` | image acquisition, preprocessing | ❌ No — do NOT add execution logic |

If you overload these with execution responsibilities, you will:

- break Phase 11  
- violate single‑responsibility  
- create naming confusion  
- create migration pain  
- create test failures  

### ✔ Phase 12 should introduce **new services**:

- `ExecutionService` or `PluginExecutionService`  
- `JobExecutionService`  
- `AnalysisExecutionService` (if needed)

These sit *alongside* the existing ones, not inside them.

### **This is the safest, cleanest, most future‑proof approach.**

---

# ⭐ 2. **PluginRegistry (Phase 11) Already Exists**  
### *Should Phase 12 add new metrics methods or is it already complete?*

### ✅ **Extend the existing registry — do NOT replace it.**

Your Phase 11 registry already has:

- success_count  
- error_count  
- execution times  
- lifecycle states  
- RWLock thread safety  

This is *excellent* — it means Phase 12 only needs to add:

### ✔ A single new method:

```python
update_execution_metrics(plugin_name, state, elapsed_ms, had_error)
```

Everything else is already there.

### ❌ Do NOT create a new registry  
### ❌ Do NOT fork the registry  
### ❌ Do NOT duplicate metrics  

Just add the Phase 12 method and reuse the existing fields.

---

# ⭐ 3. **ToolRunner Doesn’t Exist**  
### *Should it be a new class or extend existing sandbox code?*

### ✅ **Create a brand‑new class.**

Location:

```
server/app/plugins/runtime/tool_runner.py
```

Why new?

- ToolRunner is a **Phase 12 governance primitive**  
- It must be **isolated**  
- It must be **auditable**  
- It must be **testable**  
- It must be **the single choke point**  

Extending sandbox code would:

- pollute the execution path  
- break Phase 11  
- make governance impossible  

### ✔ New class  
### ✔ New file  
### ✔ New tests  
### ✔ New execution path  

---

# ⭐ 4. **Test Organization**  
### *Where should Phase 12 tests live?*

### Best practice:

```
server/tests/phase_12/
```

Why?

- Phase 12 is a **governance layer**, not a plugin or service feature  
- It needs **isolated tests**  
- It needs **clear separation from Phase 11**  
- It needs **mechanical enforcement**  

### ❌ Do NOT put them in:
- `tests/plugins/` → wrong domain  
- `tests/services/` → mixes Phase 11 and Phase 12  
- `tests/execution/` → unclear naming  

### ✔ Use a dedicated Phase 12 folder  
This matches your Phase 6–11 structure.

---

# ⭐ 5. **API Routes**  
### *Should Phase 12 add routes to existing router or create new ones?*

### Recommended:

### ✔ Create a new router file:

```
server/app/api/routes/analysis_execution.py
```

And mount it in `main.py`:

```python
app.include_router(analysis_execution.router)
```

Why?

- Phase 11 routes must remain untouched  
- Phase 12 introduces new execution semantics  
- You avoid breaking existing clients  
- You maintain backward compatibility  

### ❌ Do NOT modify existing Phase 11 routes  
Unless you want to break clients.

---

# ⭐ 6. **Which should I tackle FIRST?**  
### *To avoid guessing and rework.*

Here is the **correct order** — the one that guarantees no Phase 11 breakage and no circular dependencies.

---

# 🥇 **Step 1 — Implement ToolRunner**  
This is the foundation.  
Everything else depends on it.

---

# 🥈 **Step 2 — Extend PluginRegistry**  
Add:

```python
update_execution_metrics(...)
```

Do NOT modify existing fields.

---

# 🥉 **Step 3 — Create NEW execution services**  
- `PluginExecutionService`
- `JobExecutionService`
- `AnalysisExecutionService`

These wrap ToolRunner and preserve Phase 11 services.

---

# 🏅 **Step 4 — Add new API route**  
`analysis_execution.py`

This ensures Phase 11 routes remain untouched.

---

# 🧪 **Step 5 — Add Phase 12 tests**  
In:

```
server/tests/phase_12/
```

---

# 🔍 **Step 6 — Add mechanical scanner**  
Enforce:

- no direct plugin.run  
- ToolRunner invariants  
- metrics in finally block  

---

# 🚦 **Step 7 — Add CI pipeline + pre‑commit hook**  
This locks Phase 12 into the repo.

---

# ⭐ Final Answer Summary

| Question | Final Answer |
|---------|--------------|
| Should Phase 12 create new services? | **YES — new services. Do NOT modify existing ones.** |
| Should I extend the existing registry? | **YES — add one method, reuse existing fields.** |
| Should ToolRunner be new? | **YES — new class, new file.** |
| Where should tests go? | **server/tests/phase_12/** |
| Should API routes be new? | **YES — new router file.** |
| What should I do first? | **ToolRunner → Registry → New Services → New API → Tests → Scanner → CI** |

---

Roger, this is the moment where Phase 12 stops being abstract and becomes a **real subsystem** in your repo.  
You’re asking for four things that together form the *operational backbone* of Phase 12:

- **New Phase 12 service names + file paths**  
- **Exact Phase 12 folder structure**  
- **Final execution diagram**  
- **Phase 12 integration test suite**

Let’s build them cleanly, decisively, and in a way that respects your existing Phase 11 architecture.

---

# ⭐ 1. **NEW PHASE 12 SERVICE NAMES + FILE PATHS**

Because your existing services already have Phase‑11 responsibilities, Phase 12 must **not** modify or overload them.  
So we introduce **new execution‑focused services**, each with a single responsibility.

### ✔ **PluginExecutionService**  
Handles plugin execution orchestration (delegates to ToolRunner).

```
server/app/services/execution/plugin_execution_service.py
```

### ✔ **JobExecutionService**  
Handles job lifecycle + execution (delegates to PluginExecutionService).

```
server/app/services/execution/job_execution_service.py
```

### ✔ **AnalysisExecutionService**  
Handles API‑level execution requests (delegates to JobExecutionService).

```
server/app/services/execution/analysis_execution_service.py
```

### ✔ **ToolRunner**  
Governed execution choke‑point.

```
server/app/plugins/runtime/tool_runner.py
```

### ✔ **Phase 12 Validation + Error Envelope**  
Already defined:

```
server/app/phase12/validation.py
server/app/phase12/error_envelope.py
```

### ✔ **Phase 12 API Route**

```
server/app/api/routes/analysis_execution.py
```

These names avoid collisions with Phase 11 and preserve your existing architecture.

---

# ⭐ 2. **EXACT PHASE 12 FOLDER STRUCTURE**

Here is the **canonical Phase 12 directory layout**, matching your real repo:

```
server/
  app/
    plugins/
      runtime/
        tool_runner.py

    phase12/
      validation.py
      error_envelope.py

    services/
      execution/
        plugin_execution_service.py
        job_execution_service.py
        analysis_execution_service.py

    api/
      routes/
        analysis_execution.py

tests/
  phase_12/
    test_toolrunner.py
    test_validation.py
    test_error_envelope.py
    test_plugin_execution_service.py
    test_job_execution_service.py
    test_analysis_execution_service.py
    test_api_execution_route.py
    test_registry_metrics.py
    test_no_direct_plugin_run.py
```

This structure:

- Keeps Phase 12 isolated  
- Avoids breaking Phase 11  
- Makes governance auditable  
- Makes CI scanning trivial  

---

# ⭐ 3. **FINAL EXECUTION DIAGRAM (Phase 12)**  
This is the **authoritative execution flow** for your system.

```
┌──────────────────────────────┐
│        API Layer             │
│  /v1/analyze-execution       │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│  AnalysisExecutionService    │
│  - validates request shape   │
│  - creates job               │
│  - delegates to JobExecSvc   │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│     JobExecutionService      │
│  - loads job                 │
│  - sets RUNNING              │
│  - delegates to PluginExec   │
│  - updates job status        │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│   PluginExecutionService     │
│  - selects plugin            │
│  - delegates to ToolRunner   │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│         ToolRunner           │
│  - input validation          │
│  - plugin.run()              │
│  - output validation         │
│  - error envelope            │
│  - registry metrics          │
│  - lifecycle state           │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│        PluginRegistry        │
│  - metrics update            │
│  - lifecycle update          │
│  - thread-safe (RWLock)      │
└──────────────────────────────┘
```

This diagram is the **Phase 12 invariant**.  
If any part of this chain is bypassed, Phase 12 is broken.

---

# ⭐ 4. **PHASE 12 INTEGRATION TEST SUITE**

These are the **integration tests**, not unit tests.  
They verify the *entire execution pipeline* works end‑to‑end.

Below is the full suite outline with test names and purposes.

---

## ✔ `test_phase12_execution_flow.py`

**Purpose:**  
Verify the entire execution path from API → ToolRunner → Registry.

**Covers:**

- API route works  
- Services delegate correctly  
- ToolRunner invoked  
- Registry metrics updated  
- Structured errors returned  

---

## ✔ `test_phase12_successful_execution.py`

**Purpose:**  
Verify a plugin that returns valid output produces:

- HTTP 200  
- correct result  
- no error envelope  
- registry success_count++  

---

## ✔ `test_phase12_failed_execution.py`

**Purpose:**  
Verify plugin exceptions produce:

- HTTP 400  
- structured error envelope  
- registry error_count++  
- state = ERROR  

---

## ✔ `test_phase12_validation_integration.py`

**Purpose:**  
Verify invalid input:

- fails in ToolRunner  
- returns structured error  
- registry metrics still update  
- plugin.run() is never called  

---

## ✔ `test_phase12_registry_metrics_integration.py`

**Purpose:**  
Verify:

- last_execution_time_ms updated  
- avg_execution_time_ms updated  
- last_used updated  
- state transitions correct  

---

## ✔ `test_phase12_no_direct_plugin_run.py`

**Purpose:**  
Verify mechanical governance:

- grep for `plugin.run(`  
- ensure only ToolRunner contains it  

---

## ✔ `test_phase12_job_execution_lifecycle.py`

**Purpose:**  
Verify job lifecycle:

- PENDING → RUNNING → SUCCESS  
- PENDING → RUNNING → FAILED  

---

## ✔ `test_phase12_api_contract.py`

**Purpose:**  
Verify API response shape:

- success: `{ result, plugin }`  
- error: `{ detail: { type, message, ... } }`  

---

### 1. Phase 12 service code (final, drop‑in ready)

#### `server/app/services/execution/plugin_execution_service.py`

```python
from typing import Any, Dict, Tuple

from app.plugins.runtime.tool_runner import ToolRunner
from app.plugins.loader.plugin_registry import get_registry


class PluginExecutionService:
    """
    Phase 12: orchestrates plugin execution via ToolRunner.
    Does NOT call plugin.run() directly.
    """

    def __init__(self) -> None:
        self._registry = get_registry()
        self._runner = ToolRunner()

    def execute(
        self,
        plugin_name: str,
        payload: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Execute a plugin by name using ToolRunner.

        Returns:
            (result, error) where exactly one is non-empty.
        """
        # No direct plugin.run() here.
        return self._runner.run(plugin_name=plugin_name, payload=payload)
```

---

#### `server/app/services/execution/job_execution_service.py`

```python
from typing import Any, Dict, Tuple
from uuid import uuid4

from app.services.execution.plugin_execution_service import PluginExecutionService


class JobExecutionService:
    """
    Phase 12: manages in-memory job lifecycle + execution.
    Does NOT call ToolRunner or plugin.run() directly.
    """

    def __init__(self) -> None:
        self._plugin_exec = PluginExecutionService()
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

        result, error = self._plugin_exec.execute(
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

#### `server/app/services/execution/analysis_execution_service.py`

```python
from typing import Any, Dict, Tuple

from app.services.execution.job_execution_service import JobExecutionService


class AnalysisExecutionService:
    """
    Phase 12: API-facing execution service.
    Delegates to JobExecutionService.
    """

    def __init__(self) -> None:
        self._jobs = JobExecutionService()

    def analyze(
        self,
        plugin_name: str,
        payload: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        job_id = self._jobs.create_job(plugin_name=plugin_name, payload=payload)
        result, error = self._jobs.run_job(job_id)
        return result, error
```

---

#### `server/app/api/routes/analysis_execution.py`

```python
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from app.services.execution.analysis_execution_service import AnalysisExecutionService

router = APIRouter()
_service = AnalysisExecutionService()


@router.post("/v1/analyze-execution")
async def analyze_execution(payload: Dict[str, Any]):
    """
    Phase 12: governed execution endpoint.
    Returns structured success or structured error.
    """
    plugin_name = payload.get("plugin", "default")
    result, error = _service.analyze(plugin_name=plugin_name, payload=payload)

    if error:
        # Structured error envelope from ToolRunner.
        raise HTTPException(status_code=400, detail=error["error"])

    return {
        "result": result,
        "plugin": plugin_name,
    }
```

And in `server/app/main.py` (or equivalent):

```python
from fastapi import FastAPI
from app.api.routes import analysis_execution

app = FastAPI()
app.include_router(analysis_execution.router)
```

---

### 2. Phase 12 integration test suite (full code)

Assuming `tests/phase_12/`:

#### `tests/phase_12/test_phase12_execution_flow.py`

```python
from fastapi.testclient import TestClient

from app.main import app
from app.plugins.loader.plugin_registry import get_registry


client = TestClient(app)


class _HappyPlugin:
    def run(self, payload):
        return {"ok": True, "echo": payload.get("mime_type")}


def test_phase12_execution_flow(monkeypatch):
    reg = get_registry()
    reg.register("happy_plugin", _HappyPlugin())

    resp = client.post(
        "/v1/analyze-execution",
        json={
            "plugin": "happy_plugin",
            "image": "BASE64_PLACEHOLDER",
            "mime_type": "image/png",
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["plugin"] == "happy_plugin"
    assert body["result"]["ok"] is True
    assert body["result"]["echo"] == "image/png"
```

---

#### `tests/phase_12/test_phase12_failed_execution.py`

```python
from fastapi.testclient import TestClient

from app.main import app
from app.plugins.loader.plugin_registry import get_registry


client = TestClient(app)


class _ExplodingPlugin:
    def run(self, payload):
        raise RuntimeError("boom")


def test_phase12_failed_execution(monkeypatch):
    reg = get_registry()
    reg.register("exploding_plugin", _ExplodingPlugin())

    resp = client.post(
        "/v1/analyze-execution",
        json={
            "plugin": "exploding_plugin",
            "image": "BASE64_PLACEHOLDER",
            "mime_type": "image/png",
        },
    )

    assert resp.status_code == 400
    body = resp.json()
    assert "detail" in body
    detail = body["detail"]
    assert "type" in detail
    assert "message" in detail
    assert detail["message"] == "boom"
```

---

#### `tests/phase_12/test_phase12_validation_integration.py`

```python
from fastapi.testclient import TestClient

from app.main import app
from app.plugins.loader.plugin_registry import get_registry


client = TestClient(app)


class _NeverCalledPlugin:
    def __init__(self):
        self.called = False

    def run(self, payload):
        self.called = True
        return {"ok": True}


def test_phase12_invalid_input_never_calls_plugin(monkeypatch):
    reg = get_registry()
    plugin = _NeverCalledPlugin()
    reg.register("never_called", plugin)

    resp = client.post(
        "/v1/analyze-execution",
        json={
            "plugin": "never_called",
            "image": "",  # invalid
            "mime_type": "image/png",
        },
    )

    assert resp.status_code == 400
    assert plugin.called is False
    body = resp.json()
    assert "detail" in body
    assert body["detail"]["type"] == "ValidationError"
```

---

#### `tests/phase_12/test_phase12_registry_metrics_integration.py`

```python
from fastapi.testclient import TestClient
import time

from app.main import app
from app.plugins.loader.plugin_registry import get_registry


client = TestClient(app)


class _SlowPlugin:
    def run(self, payload):
        time.sleep(0.01)
        return {"ok": True}


def test_phase12_registry_metrics_integration(monkeypatch):
    reg = get_registry()
    reg.register("slow_plugin", _SlowPlugin())

    resp = client.post(
        "/v1/analyze-execution",
        json={
            "plugin": "slow_plugin",
            "image": "BASE64_PLACEHOLDER",
            "mime_type": "image/png",
        },
    )
    assert resp.status_code == 200

    status = reg.get_status("slow_plugin")
    assert status is not None
    assert status["success_count"] >= 1
    assert status["last_execution_time_ms"] is not None
    assert status["avg_execution_time_ms"] is not None
    assert status["last_used"] is not None
    assert status["state"] == "SUCCESS"
```

---

#### `tests/phase_12/test_phase12_job_execution_lifecycle.py`

```python
from app.services.execution.job_execution_service import JobExecutionService


class _FakePluginExecService:
    def __init__(self, result, error):
        self.result = result
        self.error = error
        self.called = False

    def execute(self, plugin_name, payload):
        self.called = True
        return self.result, self.error


def test_job_execution_success(monkeypatch):
    svc = JobExecutionService()

    fake = _FakePluginExecService({"ok": True}, {})
    monkeypatch.setattr(svc, "_plugin_mgmt__dummy", None, raising=False)  # no-op
    monkeypatch.setattr(svc, "_plugin_mgmt", fake)

    job_id = svc.create_job("fake", {"image": b"123", "mime_type": "image/png"})
    result, error = svc.run_job(job_id)

    assert result == {"ok": True}
    assert error == {}
    job = svc.get_job(job_id)
    assert job["status"] == "SUCCESS"


def test_job_execution_failure(monkeypatch):
    svc = JobExecutionService()

    fake = _FakePluginExecService({}, {"error": {"type": "ExecutionError", "message": "boom"}})
    monkeypatch.setattr(svc, "_plugin_mgmt__dummy", None, raising=False)
    monkeypatch.setattr(svc, "_plugin_mgmt", fake)

    job_id = svc.create_job("fake", {"image": b"123", "mime_type": "image/png"})
    result, error = svc.run_job(job_id)

    assert result == {}
    assert "error" in error
    job = svc.get_job(job_id)
    assert job["status"] == "FAILED"
```

---

#### `tests/phase_12/test_phase12_api_contract.py`

```python
from fastapi.testclient import TestClient

from app.main import app
from app.plugins.loader.plugin_registry import get_registry


client = TestClient(app)


class _ContractPlugin:
    def run(self, payload):
        return {"value": 42}


def test_phase12_api_success_contract(monkeypatch):
    reg = get_registry()
    reg.register("contract_plugin", _ContractPlugin())

    resp = client.post(
        "/v1/analyze-execution",
        json={
            "plugin": "contract_plugin",
            "image": "BASE64_PLACEHOLDER",
            "mime_type": "image/png",
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert "result" in body
    assert "plugin" in body
    assert body["plugin"] == "contract_plugin"
    assert body["result"]["value"] == 42
```

---

#### `tests/phase_12/test_phase12_no_direct_plugin_run.py`

```python
import pathlib
import re


def test_no_direct_plugin_run_outside_toolrunner():
    root = pathlib.Path(__file__).resolve().parents[2] / "app"
    pattern = re.compile(r"plugin\.run\(")
    violations = []

    for path in root.rglob("*.py"):
        if "tool_runner.py" in str(path):
            continue
        text = path.read_text(encoding="utf-8")
        if pattern.search(text):
            violations.append(str(path))

    assert not violations, f"Direct plugin.run() calls found: {violations}"
```

---

### 3. Phase 12 migration guide

```md
# Phase 12 Migration Guide

## Goal

Introduce governed plugin execution via ToolRunner and new execution services, without breaking Phase 11.

---

## Step 1 — Add ToolRunner

- Create `server/app/plugins/runtime/tool_runner.py`.
- Implement:
  - input validation
  - plugin.run()
  - output validation
  - error envelope
  - registry metrics update in finally block

---

## Step 2 — Extend PluginRegistry

- In `plugin_registry.py`:
  - Add `update_execution_metrics(plugin_name, state, elapsed_ms, had_error)`.
  - Reuse existing metrics fields (success_count, error_count, timings, state).
  - Do not remove or rename any Phase 11 fields.

---

## Step 3 — Add Execution Services

- Create:
  - `services/execution/plugin_execution_service.py`
  - `services/execution/job_execution_service.py`
  - `services/execution/analysis_execution_service.py`
- Ensure:
  - No direct plugin.run() calls.
  - Only ToolRunner is used for execution.

---

## Step 4 — Add Execution API Route

- Create `api/routes/analysis_execution.py`.
- Mount in `main.py` via `include_router`.
- Do not modify existing Phase 11 routes.

---

## Step 5 — Add Phase 12 Tests

- Create `tests/phase_12/` with:
  - execution flow tests
  - validation integration tests
  - registry metrics tests
  - API contract tests
  - no-direct-plugin-run test

---

## Step 6 — Add Mechanical Scanner

- Add `scripts/scan_phase_12_violations.py`.
- Wire into:
  - CI pipeline
  - optional pre-commit hook

---

## Step 7 — Run Full Suite

- `python scripts/scan_phase_12_violations.py`
- `pytest tests/phase_11`
- `pytest tests/phase_12`

Phase 12 is complete when all pass.
```

---

### 4. Phase 12 contributor onboarding guide

```md
# Phase 12 Contributor Onboarding

Welcome to Phase 12 — the execution governance layer.

This guide explains how to work safely within the new constraints.

---

## 1. Core Principle

All plugin execution MUST go through ToolRunner.

Forbidden:
- Direct `plugin.run()` calls outside ToolRunner.
- Bypassing validation or error wrapping.
- Bypassing registry metrics.

---

## 2. Where Things Live

- ToolRunner:
  - `app/plugins/runtime/tool_runner.py`
- Validation & Error Envelope:
  - `app/phase12/validation.py`
  - `app/phase12/error_envelope.py`
- Execution Services:
  - `app/services/execution/plugin_execution_service.py`
  - `app/services/execution/job_execution_service.py`
  - `app/services/execution/analysis_execution_service.py`
- API Route:
  - `app/api/routes/analysis_execution.py`
- Tests:
  - `tests/phase_12/`

---

## 3. How to Execute a Plugin (Correct Way)

From services or API:

```python
from app.services.execution.plugin_execution_service import PluginExecutionService

svc = PluginExecutionService()
result, error = svc.execute("my_plugin", payload)
```

Never:

```python
plugin = registry.get_plugin("my_plugin")
plugin.run(payload)  # ❌ forbidden
```

---

## 4. Error Handling

- Do not catch exceptions around ToolRunner unless converting to HTTP errors.
- Do not construct your own error envelopes.
- Always pass through the `error` dict returned by ToolRunner.

---

## 5. Adding New Plugins

- Register plugin in existing registry.
- Ensure plugin returns a dict.
- Do not perform HTTP or DB side effects in ToolRunner; keep plugins focused.

---

## 6. Tests You Must Run

Before pushing:

- `python scripts/scan_phase_12_violations.py`
- `pytest tests/phase_11`
- `pytest tests/phase_12`

If scanner fails, fix violations before committing.

---

## 7. When in Doubt

Ask yourself:

- “Am I calling ToolRunner for execution?”
- “Am I returning structured errors?”
- “Am I updating metrics via ToolRunner only?”

If any answer is “no”, you’re outside Phase 12 rules.
```

---

### 5. Phase 12 ASCII architecture poster

```text
========================================================
                 PHASE 12 ARCHITECTURE
        Governed Plugin Execution & Observability
========================================================

          ┌────────────────────────────────────┐
          │            HTTP Client             │
          └─────────────────┬──────────────────┘
                            │
                            ▼
          ┌────────────────────────────────────┐
          │        API Layer (FastAPI)         │
          │  /v1/analyze-execution             │
          └─────────────────┬──────────────────┘
                            │
                            ▼
          ┌────────────────────────────────────┐
          │   AnalysisExecutionService         │
          │  - orchestrates high-level call    │
          │  - delegates to JobExecutionSvc    │
          └─────────────────┬──────────────────┘
                            │
                            ▼
          ┌────────────────────────────────────┐
          │       JobExecutionService          │
          │  - manages job lifecycle           │
          │  - PENDING → RUNNING → SUCCESS/FAIL│
          │  - delegates to PluginExecutionSvc │
          └─────────────────┬──────────────────┘
                            │
                            ▼
          ┌────────────────────────────────────┐
          │     PluginExecutionService         │
          │  - selects plugin by name          │
          │  - delegates to ToolRunner         │
          └─────────────────┬──────────────────┘
                            │
                            ▼
          ┌────────────────────────────────────┐
          │             ToolRunner             │
          │  - input validation                │
          │  - plugin.run()                    │
          │  - output validation               │
          │  - error envelope                  │
          │  - registry metrics + lifecycle    │
          └─────────────────┬──────────────────┘
                            │
                            ▼
          ┌────────────────────────────────────┐
          │          PluginRegistry            │
          │  - plugin lookup                   │
          │  - success/error counts            │
          │  - execution timings               │
          │  - last_used, state                │
          │  - RWLock thread safety            │
          └────────────────────────────────────┘

========================================================
Invariant: NO direct plugin.run() outside ToolRunner.
All errors are structured. All executions are measured.
========================================================
```

REMEBER repace phase12 folder and file names to functionality or behaviour dont use phaase12 in any of the server or sweb-ui diirectories