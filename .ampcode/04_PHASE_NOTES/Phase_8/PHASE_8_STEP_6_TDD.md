# Phase 8 — Step 6 TDD
## Device Selector (CPU/GPU + Fallback Logging)

**Status:** Planned  
**Depends on:** Step 5 (FPS controls) → Performance baselines  
**Unlocks:** Phase 8 Closure

---

## Purpose

Allow users to choose CPU/GPU and log all device-related decisions:
- ✅ Device selector in UI (dropdown: CPU, GPU, Auto)
- ✅ Device param wired through API → Pipeline → Plugin
- ✅ Fallback logging with job_id + correlation IDs
- ✅ Device usage metrics → DuckDB
- ✅ GPU → CPU fallback on failure (graceful degradation)

---

## TDD Cycle

### 1. RED — First Failing Test

**File:** `server/tests/device_selector/test_device_selector_propagates.py`

**Test:**
```python
def test_device_param_propagates_to_job_pipeline():
    """Verify device='gpu' reaches the job pipeline."""
    from app.services.job_management_service import run_job
    
    job = run_job(
        plugin="ocr",
        input_data={"image": b"..."},
        device="gpu"
    )
    
    # Job must have device set
    assert job.device == "gpu"
```

This test **must fail** (no device param support yet).

---

### 2. GREEN — Minimal Implementation

**File:** `server/app/api/v1/analyze.py` (modify existing endpoint)

**Changes:**
```python
from fastapi import APIRouter, Query

router = APIRouter()

@router.post("/v1/analyze")
async def analyze(
    plugin: str,
    tool: str,
    image_b64: str,
    device: str = Query("cpu", regex="^(cpu|gpu|auto)$")
):
    """Analyze image with plugin + tool.
    
    Args:
        device: Execution device ("cpu", "gpu", "auto")
    """
    job = await run_job(
        plugin=plugin,
        tool=tool,
        input_data={"image": image_b64},
        device=device
    )
    return job
```

**Goal:** Pass device param through to job pipeline.

---

### 3. REFACTOR — Add Fallback Logic + Metrics

**Additional tests:**

#### Test: GPU failure falls back to CPU
```python
def test_gpu_failure_falls_back_to_cpu(monkeypatch):
    """Verify GPU failure triggers CPU fallback."""
    # Mock GPU execution failure
    def mock_execute(plugin, tool, input_data, device):
        if device == "gpu":
            raise RuntimeError("CUDA not available")
        return {"boxes": [...], "scores": [...], "labels": [...]}
    
    monkeypatch.setattr("app.plugins.runner.execute_plugin_tool", mock_execute)
    
    job = run_job(
        plugin="ocr",
        input_data={"image": b"..."},
        device="gpu"
    )
    
    # Should succeed on CPU
    assert job.status == "complete"
    # Should have fallback flag
    assert job.device_fallback == True
```

#### Test: Fallback logged with job_id
```python
def test_fallback_logged_with_job_id(monkeypatch):
    """Verify fallback warnings include job_id."""
    logs = []
    
    def mock_log(msg):
        logs.append(msg)
    
    monkeypatch.setattr("app.logging.warning", mock_log)
    
    # Trigger fallback
    job = run_job(
        plugin="ocr",
        input_data={"image": b"..."},
        device="gpu"  # Will fail, fall back to CPU
    )
    
    # Check logs include job_id + fallback context
    fallback_logs = [l for l in logs if "fallback" in l.lower()]
    assert any(job.id in l for l in fallback_logs)
    assert any("gpu" in l.lower() for l in fallback_logs)
    assert any("cpu" in l.lower() for l in fallback_logs)
```

#### Test: Device usage metric written
```python
def test_device_usage_metric_written():
    """Verify device_usage metric in DuckDB."""
    from app.observability.metrics_writer import MetricsWriter
    
    job = run_job(
        plugin="ocr",
        input_data={"image": b"..."},
        device="gpu"
    )
    
    # Query metrics
    conn = duckdb.connect("metrics.db")
    result = conn.execute(
        "SELECT * FROM device_usage WHERE job_id = ?",
        [job.id]
    ).fetchall()
    
    assert len(result) > 0
    assert result[0]["device_requested"] == "gpu"
    assert result[0]["device_used"] in ["gpu", "cpu"]
    assert result[0]["fallback"] == (result[0]["device_requested"] != result[0]["device_used"])
```

---

### 4. Integration Tests

**File:** `server/tests/device_selector/test_device_selector_integration.py`

#### Test: UI → API → Pipeline → Plugin → Metrics
```python
async def test_device_selector_end_to_end(client, db):
    """Full E2E device selector flow."""
    # UI sends request with device="gpu"
    response = await client.post(
        "/v1/analyze",
        params={"device": "gpu", "plugin": "ocr", "tool": "extract_text"},
        json={"image": "base64-image-data"}
    )
    
    job_id = response.json()["id"]
    
    # API returns job with device info
    assert response.status_code == 200
    assert response.json()["device"] == "gpu"
    
    # Pipeline processed job
    assert response.json()["status"] == "complete"
    
    # Metrics stored
    metrics = db.query(
        "SELECT * FROM device_usage WHERE job_id = ?",
        [job_id]
    )
    assert len(metrics) > 0
```

---

## Exit Criteria

✅ Device selector dropdown in UI (CPU, GPU, Auto)  
✅ Device param wired: UI → API → Pipeline → Plugin  
✅ Fallback logic: GPU fail → CPU succeed  
✅ Fallback logged with job_id + correlation IDs  
✅ Device usage metrics in DuckDB  
✅ No broken plugins from device param  
✅ All tests passing  

Once these criteria are met, **Step 6 is complete** and Phase 8 is ready for closure.

---

## Device Selector Logic

### Request Flow
```
UI (device dropdown)
  ↓
POST /v1/analyze?device=gpu
  ↓
API validates device ∈ {cpu, gpu, auto}
  ↓
Job pipeline receives device
  ↓
Plugin receives device
  ↓
Plugin attempts to use device
  ↓
If failure: Plugin falls back + logs warning
  ↓
MetricsWriter records device_usage
```

### Fallback Behaviour

| Requested | Available | Used | Fallback | Log Level |
|-----------|-----------|------|----------|-----------|
| GPU | GPU | GPU | False | info |
| GPU | CPU only | CPU | True | warning |
| GPU | None | Error | N/A | error |
| CPU | Any | CPU | False | info |
| Auto | GPU | GPU | False | info |
| Auto | CPU | CPU | False | info |

---

## DuckDB Schema (device_usage table)

```sql
CREATE TABLE device_usage (
    id UUID PRIMARY KEY,
    job_id TEXT NOT NULL,
    device_requested TEXT NOT NULL,  -- "cpu", "gpu", "auto"
    device_used TEXT NOT NULL,       -- actual device used
    fallback BOOLEAN NOT NULL,       -- true if fallback occurred
    created_at TIMESTAMP NOT NULL
);
```

---

## UI Component (Placeholder)

```tsx
<select
  value={device}
  onChange={(e) => setDevice(e.target.value)}
  className="device-selector"
>
  <option value="auto">Auto (Best available)</option>
  <option value="cpu">CPU Only</option>
  <option value="gpu">GPU (if available)</option>
</select>
```

Wiring to be implemented in Step 6.
