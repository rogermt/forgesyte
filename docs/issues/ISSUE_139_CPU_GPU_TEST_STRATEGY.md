# ISSUE_139: CPU vs GPU Test Strategy

**Critical Understanding:** Tests are split into CPU-only (run now) and GPU-only (run Week 3 on Kaggle).

---

## The Problem

You develop on CPU. Models are stubs in GitHub. Real models only exist on Kaggle with GPU.

Therefore:
- ✅ **CPU tests:** Contract validation, manifest structure, JSON safety — **pass immediately**
- ❌ **GPU tests:** Real inference validation — **run ONLY on Kaggle Week 3**

---

## Test Organization

### CPU Tests (Run Now, Every Commit)

**These tests do NOT load models. They validate structure:**

#### forgesyte backend (`server/app`)
```bash
cd /home/rogermt/forgesyte/server

# Run WITHOUT RUN_MODEL_TESTS=1
uv run pytest tests/unit/ -v                 # ManifestCacheService tests
uv run pytest tests/integration/ -v          # Manifest endpoint, tool endpoint (dummy frames)
```

**Files:**
- `tests/unit/test_manifest_cache.py` — Cache behavior
- `tests/integration/test_plugins_manifest_yolo.py` — GET /manifest endpoint
- `tests/integration/test_plugins_run_yolo_*.py` — POST /run endpoint (dummy 10x10 frames)

**Why they pass on CPU:**
- Dummy synthetic frames (zeros arrays)
- No model loading
- No GPU needed

---

#### forgesyte-plugins (YOLO Tracker)
```bash
cd /home/rogermt/forgesyte-plugins/plugins/forgesyte-yolo-tracker

# Run WITHOUT RUN_MODEL_TESTS=1
uv run pytest src/tests/test_manifest_contract.py -v          # Manifest structure
uv run pytest src/tests/test_tool_output_contract.py -v       # Output format (dummy frames)
```

**Files:**
- `src/tests/test_manifest_contract.py` — Manifest has required fields, tools, etc.
- `src/tests/test_tool_output_contract.py` — Output is dict, JSON-safe, etc.

**Why they pass on CPU:**
- Dummy synthetic frames (zeros arrays)
- No model inference
- No GPU needed

---

### GPU Tests (Run Week 3 Only)

**These tests load real YOLO models and validate inference output:**

#### forgesyte backend (`server/tests/contract`)

```bash
# ⚠️ This runs ONLY on Kaggle with RUN_MODEL_TESTS=1
cd /kaggle/working/forgesyte/server
RUN_MODEL_TESTS=1 pytest tests/contract/ -v
```

**Files:**
- `tests/contract/test_yolo_player_detection_gpu.py` — Real inference
- `tests/contract/test_yolo_ball_detection_gpu.py` — Real inference
- `tests/contract/test_ocr_contract_gpu.py` — Real OCR processing

**Why they run ONLY on Kaggle:**
- Real YOLO models loaded
- Real inference executed
- GPU required
- Stub models in GitHub won't work

---

#### forgesyte-plugins (YOLO Tracker)

```bash
# ⚠️ This runs ONLY on Kaggle with RUN_MODEL_TESTS=1
cd /kaggle/working/forgesyte-plugins/plugins/forgesyte-yolo-tracker
RUN_MODEL_TESTS=1 pytest src/tests/integration/test_backend_contract.py -v
```

**Files:**
- `src/tests/integration/test_backend_contract.py` — Real inference with base64 frames

**Why it runs ONLY on Kaggle:**
- Real YOLO models loaded
- Real inference executed
- GPU required
- Validates real output matches contract

---

## Test Markers

### CPU Tests (No Marker Needed)

```python
# In CPU tests:
def test_manifest_structure():
    """This runs always (no marker)."""
    pass
```

### GPU Tests (Skip Marker Required)

```python
# In GPU tests:
import os
import pytest

RUN_MODEL_TESTS = os.getenv("RUN_MODEL_TESTS", "0") == "1"

pytestmark = pytest.mark.skipif(
    not RUN_MODEL_TESTS,
    reason="GPU test: Set RUN_MODEL_TESTS=1 (Kaggle only)"
)

def test_real_inference():
    """This skips on CPU, runs on Kaggle."""
    pass
```

**Behavior:**

```bash
# On CPU (without RUN_MODEL_TESTS=1):
$ uv run pytest test_backend_contract.py -v
# Output: 1 skipped

# On Kaggle (with RUN_MODEL_TESTS=1):
$ RUN_MODEL_TESTS=1 uv run pytest test_backend_contract.py -v
# Output: 1 passed (real inference)
```

---

## Workflow

### Week 1 (Now, CPU)

**forgesyte backend:**
```bash
# Commit 1-5: CPU tests, no RUN_MODEL_TESTS=1
cd /home/rogermt/forgesyte/server
git checkout -b feat/plugin-api-endpoints

# Tests pass immediately (dummy frames)
uv run pytest tests/unit/ tests/integration/ -v

# All checks pass
uv run ruff check --fix app/ tests/
uv run mypy app/ --no-site-packages
uv run pre-commit run --all-files

git commit -m "feat(api): add plugin endpoints (CPU tests)"
git push -u origin feat/plugin-api-endpoints
```

**forgesyte-plugins:**
```bash
# Commit 1-2: CPU tests only, no RUN_MODEL_TESTS=1
cd /home/rogermt/forgesyte-plugins/plugins/forgesyte-yolo-tracker
git checkout -b feat/plugin-api-endpoints

# Tests pass immediately (dummy frames)
uv run pytest src/tests/test_manifest_contract.py src/tests/test_tool_output_contract.py -v

# Commit includes GPU test (marked with skip, will be skipped)
git commit -m "test(yolo-tracker): validate plugin contract (GPU test included, skipped on CPU)"
git push -u origin feat/plugin-api-endpoints
```

---

### Week 3 (GPU, Kaggle)

**On Kaggle with real models:**

```bash
# forgesyte backend
cd /kaggle/working/forgesyte/server
RUN_MODEL_TESTS=1 pytest tests/contract/ -v
# ✅ CPU tests pass fast
# ✅ GPU tests run with real models

# forgesyte-plugins
cd /kaggle/working/forgesyte-plugins/plugins/forgesyte-yolo-tracker
RUN_MODEL_TESTS=1 pytest src/tests/ -v
# ✅ CPU tests pass fast
# ✅ GPU integration test runs with real models
```

---

## Summary Table

| Aspect | CPU Tests | GPU Tests |
|--------|-----------|-----------|
| **When** | Run now, every commit | Run Week 3, Kaggle only |
| **Models** | Stub/none | Real YOLO models |
| **Frames** | Dummy zeros arrays | Real video frames |
| **GPU** | Not needed | Required |
| **Speed** | Fast (< 1 sec) | Slow (model load + inference) |
| **Location** | This machine | Kaggle GPU |
| **Command** | `pytest tests/ -v` | `RUN_MODEL_TESTS=1 pytest tests/ -v` |
| **Skip marker** | No | Yes, `pytestmark` with `skipif` |
| **CI/CD** | ✅ Always runs | ⏭️ Skip in CI, manual Week 3 |

---

## Important Commands Reference

### CPU-Only (Right Now)

```bash
# forgesyte
cd /home/rogermt/forgesyte/server
uv run pytest tests/unit/ tests/integration/ -v

# forgesyte-plugins
cd /home/rogermt/forgesyte-plugins/plugins/forgesyte-yolo-tracker
uv run pytest src/tests/test_manifest_contract.py src/tests/test_tool_output_contract.py -v
```

### GPU (Week 3, Kaggle)

```bash
# forgesyte
cd /kaggle/working/forgesyte/server
RUN_MODEL_TESTS=1 pytest tests/contract/ -v

# forgesyte-plugins
cd /kaggle/working/forgesyte-plugins/plugins/forgesyte-yolo-tracker
RUN_MODEL_TESTS=1 pytest src/tests/integration/test_backend_contract.py -v
```

---

## Troubleshooting

**Q: GPU test runs on CPU but shouldn't?**
A: You have real models in your local environment. Either:
   - Move them: `mv ~/models .models_backup`
   - Or test expects `RUN_MODEL_TESTS=1` to be set

**Q: CPU test runs on Kaggle but should be fast?**
A: It should still be fast (< 1 sec) even on Kaggle because no models loaded.

**Q: How do I know which environment I'm in?**
A: Check for model files:
   ```bash
   ls -la plugins/forgesyte-yolo-tracker/models/
   # CPU (GitHub): Empty or stub files
   # Kaggle: Real .pt files (large, > 100MB)
   ```

---

## Key Takeaway

✅ **CPU tests** → Validate **structure and contracts** → Pass now  
⏭️ **GPU tests** → Validate **real inference** → Run Week 3 on Kaggle

This split allows development to continue on CPU while ensuring GPU correctness is verified separately with real models.
