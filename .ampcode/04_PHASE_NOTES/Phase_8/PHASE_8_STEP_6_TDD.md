# ⭐ **PHASE_8_STEP_6_TDD.md — Device Selector (Backend)**  
### *Phase 8 — Step 6: Device Selection & Fallback Strategy (TDD)*

Phase 8 Step 6 introduces **device selection** (CPU/GPU) with **automatic fallback**, **metrics logging**, and **contract-safe propagation** through the job pipeline.

---

## 1. **Purpose of Step 6**

The device selector must:

- Accept `device` parameter (`cpu` or `gpu`) at `/v1/analyze`  
- Propagate through job pipeline → plugin runner  
- Log requested vs. used device in `device_usage` DuckDB table  
- Implement automatic fallback: GPU unavailable → CPU  
- Validate device param (reject invalid values)  
- Provide metrics for observability  

This enables frontend to select device + backend to handle gracefully.

---

## 2. **TDD Cycle for Step 6**

### **RED → First failing tests**

#### Test files:
```
server/tests/api/test_device_selector.py      (API layer tests)
server/tests/services/test_device_selection.py (service layer tests)
```

#### Tests:

**API Layer (`test_device_selector.py`):**
- `test_analyze_accepts_device_cpu_param`
- `test_analyze_accepts_device_gpu_param`  
- `test_analyze_rejects_invalid_device_param`
- `test_analyze_defaults_device_to_cpu` (if not provided)

**Service Layer (`test_device_selection.py`):**
- `test_device_selection_cpu_always_works`
- `test_device_selection_gpu_fallback_to_cpu_if_unavailable`
- `test_device_selection_logs_requested_device`
- `test_device_selection_logs_actual_device_used`

These tests must fail initially.

---

### **GREEN → Minimal implementation**

#### Files to create/modify:

**1. API endpoint** (`server/app/api.py`):
- Add `device` query parameter (optional, default "cpu")
- Validate device is "cpu" or "gpu"
- Pass to `AnalysisService`

**2. Service layer** (`server/app/services/analysis_service.py`):
- Accept `device` param in `process_analysis_request()`
- Pass through to job pipeline

**3. Job pipeline** (`server/app/tasks.py`):
- Accept `device` in job context
- Store in job object

**4. Plugin runner** (`server/app/plugins/base.py`):
- Accept `device` from job context
- Check GPU availability
- Fallback to CPU if needed
- Return device actually used

**5. Observability** (`server/app/observability/duckdb/duckdb_manager.py`):
- Log `device_requested` and `device_used` in `device_usage` table

**6. Models** (`server/app/models.py`):
- Add `device` field to job request/response objects

---

### **REFACTOR → Enhance validation & observability**

Add:
- Device validation utility function
- Device availability checker (GPU detection)
- Comprehensive metrics for device selection
- Better error messages for invalid devices

Add new tests:
- `test_device_selection_gpu_detection`
- `test_device_selection_metrics_logged_correctly`
- `test_device_selection_logs_include_job_id`

---

## 3. **Step 6 Test Suite**

Place in:
```
server/tests/api/test_device_selector.py
server/tests/services/test_device_selection.py
```

### **3.1 API layer tests**

```python
# test_device_selector.py

def test_analyze_accepts_device_cpu_param(client):
    """Verify /analyze accepts device=cpu query parameter."""
    response = client.post(
        "/analyze?plugin=ocr&device=cpu",
        files={"file": ("test.png", b"fake_image")},
    )
    assert response.status_code == 200
    assert "job_id" in response.json()

def test_analyze_accepts_device_gpu_param(client):
    """Verify /analyze accepts device=gpu query parameter."""
    response = client.post(
        "/analyze?plugin=ocr&device=gpu",
        files={"file": ("test.png", b"fake_image")},
    )
    assert response.status_code == 200
    assert "job_id" in response.json()

def test_analyze_rejects_invalid_device_param(client):
    """Verify /analyze rejects device=xyz (invalid)."""
    response = client.post(
        "/analyze?plugin=ocr&device=xyz",
        files={"file": ("test.png", b"fake_image")},
    )
    assert response.status_code == 400
    assert "device" in response.json()["detail"].lower()

def test_analyze_defaults_device_to_cpu(client):
    """Verify /analyze defaults to device=cpu if not provided."""
    response = client.post(
        "/analyze?plugin=ocr",
        files={"file": ("test.png", b"fake_image")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("device_requested") == "cpu" or data.get("device") == "cpu"
```

### **3.2 Service layer tests**

```python
# test_device_selection.py

def test_device_selection_cpu_always_works(analysis_service):
    """Verify CPU device selection never fails."""
    result = asyncio.run(analysis_service.process_analysis_request(
        file_bytes=b"fake_image",
        image_url=None,
        body_bytes=None,
        plugin="ocr",
        options={},
        device="cpu",  # NEW PARAM
    ))
    assert result["job_id"]
    assert result.get("device_requested") == "cpu"

def test_device_selection_gpu_fallback_to_cpu(analysis_service):
    """Verify GPU unavailable → fallback to CPU with metrics."""
    result = asyncio.run(analysis_service.process_analysis_request(
        file_bytes=b"fake_image",
        image_url=None,
        body_bytes=None,
        plugin="ocr",
        options={},
        device="gpu",  # Request GPU
    ))
    # Should succeed and either use GPU or fallback to CPU
    assert result["job_id"]
    # If GPU unavailable, should log fallback in metrics

def test_device_selection_logs_requested_device(duckdb_manager):
    """Verify device_usage table logs device_requested."""
    # (Requires full job run to completion)
    records = duckdb_manager.query(
        "SELECT device_requested FROM device_usage LIMIT 1"
    )
    assert records[0]["device_requested"] in ["cpu", "gpu"]

def test_device_selection_logs_actual_device(duckdb_manager):
    """Verify device_usage table logs device_used."""
    records = duckdb_manager.query(
        "SELECT device_used FROM device_usage LIMIT 1"
    )
    assert records[0]["device_used"] in ["cpu", "gpu"]
```

---

## 4. **Implementation Checklist**

### **Phase 1: API Layer**
- [ ] Add `device` query parameter to `/analyze` endpoint
- [ ] Validate device is "cpu" or "gpu"
- [ ] Default to "cpu" if not provided
- [ ] Return 400 if invalid device
- [ ] Pass device to AnalysisService
- [ ] Test API layer (4 tests above)

### **Phase 2: Service Layer**
- [ ] Add `device` parameter to `process_analysis_request()`
- [ ] Pass device through job pipeline
- [ ] Test service layer (2 tests above)

### **Phase 3: Job Pipeline**
- [ ] Add `device` field to job context
- [ ] Store device in job object
- [ ] Pass to plugin runner

### **Phase 4: Plugin Runner**
- [ ] Modify `BasePlugin.run()` to accept `device` param
- [ ] Check GPU availability (try import torch, check torch.cuda.is_available())
- [ ] Fallback to CPU if GPU unavailable
- [ ] Return device actually used
- [ ] Log device decision

### **Phase 5: Observability**
- [ ] Ensure `device_usage` table exists (already in schema)
- [ ] Log job_id, device_requested, device_used
- [ ] Log timestamp
- [ ] Ensure metrics include device info

### **Phase 6: Models**
- [ ] Add `device` field to `PluginToolRunRequest`
- [ ] Add `device_requested` and `device_used` to response models

---

## 5. **Contract & Schema**

### **Updated API endpoint:**

```
POST /v1/analyze?plugin={name}&device={cpu|gpu}
```

**Query parameters:**
- `plugin` (required): Plugin name (e.g., "ocr")
- `device` (optional, default "cpu"): "cpu" or "gpu"
- `image_url` (optional): Remote image URL
- `options` (optional): JSON string of plugin options

**Response:**
```json
{
  "job_id": "uuid",
  "status": "pending",
  "plugin": "ocr",
  "device_requested": "gpu",
  "device_used": "cpu"  // Actual device after fallback
}
```

### **DuckDB Schema** (already exists):

```sql
CREATE TABLE device_usage (
  job_id UUID,
  device_requested TEXT,
  device_used TEXT,
  fallback BOOLEAN,
  timestamp TIMESTAMP
);
```

---

## 6. **Implementation Notes**

### **GPU Detection**
```python
def get_gpu_available() -> bool:
    """Check if GPU is available."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False
```

### **Device Validation**
```python
def validate_device(device: str) -> bool:
    """Validate device is 'cpu' or 'gpu'."""
    return device.lower() in ["cpu", "gpu"]
```

### **Fallback Logic**
```python
def resolve_device(requested: str, gpu_available: bool) -> str:
    """Resolve requested device to actual device."""
    if requested == "gpu" and not gpu_available:
        logger.warning(f"GPU requested but unavailable, falling back to CPU")
        return "cpu"
    return requested
```

---

## 7. **Integration Points**

After Step 6 is complete:

- `api.py` → accepts `device` query param  
- `AnalysisService` → propagates device  
- `tasks.py` → stores device in job  
- `BasePlugin.run()` → receives device, returns device_used  
- `device_usage` table → logs all device selections  
- Web UI (Step 7) → provides dropdown to select device  

This unlocks Step 7 (Web UI Device Selector).

---

## 8. **Exit Criteria for Step 6**

- [ ] All Step 6 tests green (API + Service + Observability)
- [ ] `device` parameter accepted by `/v1/analyze`
- [ ] Invalid devices rejected with 400
- [ ] Valid devices propagated through pipeline
- [ ] GPU fallback to CPU when unavailable
- [ ] `device_usage` table populated with requests/actuals
- [ ] All logs include device info
- [ ] No breaking changes to existing endpoints
- [ ] Contract matches `.ampcode` spec
- [ ] Metrics complete and queryable

Once these are met, Step 6 is complete and Step 7 (Web UI Device Selector) is unblocked.

---

## 9. **Next Steps**

After Step 6 backend:

- **Step 7:** Web UI Device Selector dropdown (calls `/v1/analyze?device=`)
- **Step 8:** Device metrics dashboard (query `device_usage` table)
- **Step 9:** Advanced device scheduling (queue GPU jobs, fallback CPU immediately)

---

## Annotations

**Deviation:** None yet (Step 6 is just starting).  
**Decision:** Implement device selection server-side first, UI dropdown second commit.  
**Reason:** Stable backend contract first, UI follows naturally.

---
