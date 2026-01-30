# ISSUE_139 Quick Reference

## Test Split: CPU vs GPU

| When | What | Where | Command | Models |
|------|------|-------|---------|--------|
| **NOW** | CPU tests | This machine | `uv run pytest tests/ -v` | Stub/none |
| **Week 3** | GPU tests | Kaggle | `RUN_MODEL_TESTS=1 pytest tests/contract/ -v` | Real YOLO |

---

## CPU Tests (Run Now)

### forgesyte backend
```bash
cd /home/rogermt/forgesyte/server
uv run pytest tests/unit/ tests/integration/ -v
# ✅ No RUN_MODEL_TESTS=1 needed
# ✅ Dummy frames (10x10 zeros)
# ✅ < 5 seconds
```

### forgesyte-plugins
```bash
cd /home/rogermt/forgesyte-plugins/plugins/forgesyte-yolo-tracker
uv run pytest src/tests/test_manifest_contract.py src/tests/test_tool_output_contract.py -v
# ✅ No RUN_MODEL_TESTS=1 needed
# ✅ Dummy frames (480x640 zeros)
# ✅ < 10 seconds
```

---

## GPU Tests (Week 3 on Kaggle)

### forgesyte backend
```bash
cd /kaggle/working/forgesyte/server
RUN_MODEL_TESTS=1 pytest tests/contract/ -v
# ✅ RUN_MODEL_TESTS=1 required
# ✅ Real YOLO models loaded
# ✅ Real inference
```

### forgesyte-plugins
```bash
cd /kaggle/working/forgesyte-plugins/plugins/forgesyte-yolo-tracker
RUN_MODEL_TESTS=1 pytest src/tests/integration/test_backend_contract.py -v
# ✅ RUN_MODEL_TESTS=1 required
# ✅ Real YOLO models loaded
# ✅ Real inference
```

---

## Test Marker Pattern

**CPU Test (no marker):**
```python
def test_manifest_structure():
    """Always runs."""
    pass
```

**GPU Test (with marker):**
```python
import os
import pytest

RUN_MODEL_TESTS = os.getenv("RUN_MODEL_TESTS", "0") == "1"

pytestmark = pytest.mark.skipif(
    not RUN_MODEL_TESTS,
    reason="GPU test: Set RUN_MODEL_TESTS=1"
)

def test_real_inference():
    """Skips on CPU, runs on Kaggle."""
    pass
```

---

## Branches

Both repos use **same branch name**: `feat/plugin-api-endpoints`

```bash
# forgesyte
cd /home/rogermt/forgesyte
git checkout -b feat/plugin-api-endpoints

# forgesyte-plugins
cd /home/rogermt/forgesyte-plugins
git checkout -b feat/plugin-api-endpoints
```

---

## Files to Create

### forgesyte (5 commits)
- ✅ `server/app/services/manifest_cache.py`
- ✅ `server/app/api_plugins.py`
- ✅ `server/tests/unit/test_manifest_cache.py`
- ✅ `server/tests/integration/test_plugins_manifest_yolo.py`
- ✅ `server/tests/integration/test_plugins_run_yolo_*.py`

### forgesyte-plugins (3 commits, 2 CPU + 1 GPU)
- ✅ `plugins/forgesyte-yolo-tracker/src/tests/test_manifest_contract.py`
- ✅ `plugins/forgesyte-yolo-tracker/src/tests/test_tool_output_contract.py`
- ✅ `plugins/forgesyte-yolo-tracker/src/tests/integration/test_backend_contract.py` **(GPU-only)**

---

## Commit Timeline

### Week 1 (CPU, This Machine)

**forgesyte backend:**
- Commit 1: ManifestCacheService (unit test)
- Commit 2: GET /manifest endpoint
- Commit 3: POST /run endpoint
- Commit 4: Tests for all YOLO tools
- Commit 5: Verification

**forgesyte-plugins:**
- Commit 1: Manifest validation test
- Commit 2: Output format test
- Commit 3: GPU integration test (skipped on CPU)

### Week 3 (GPU, Kaggle)

- Run GPU tests with real models
- Verify end-to-end pipeline

---

## Key Insight

**CPU tests validate the CONTRACT** (is the API shape correct?)  
**GPU tests validate the IMPLEMENTATION** (do real models work with it?)

Both needed, but at different times with different infrastructure.

---

## Verify You're Ready

```bash
# Check CPU tests pass (no RUN_MODEL_TESTS=1)
cd /home/rogermt/forgesyte/server
uv run pytest tests/unit/ tests/integration/ -v

cd /home/rogermt/forgesyte-plugins/plugins/forgesyte-yolo-tracker
uv run pytest src/tests/test_manifest_contract.py src/tests/test_tool_output_contract.py -v

# Check GPU test is skipped (no real models)
uv run pytest src/tests/integration/test_backend_contract.py -v
# Should show: "1 skipped"
```

✅ If all pass/skip correctly, you're ready for Week 3 GPU testing!
