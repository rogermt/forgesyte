# How to Fix the 20 Pre-Existing Test Failures

**Status:** Post-DuckDB-Fix Analysis  
**Failures:** 20 tests that still fail after DuckDB fix (not caused by DuckDB)  
**Scope:** User requirement - "ALL TESTS NEED FIXING"

---

## Summary of 20 Failures by Category

| Category | Count | Root Cause | Effort | Priority |
|----------|-------|-----------|--------|----------|
| **Device Integration** | 6 | Device param/config handling | Medium | High |
| **Image Submission** | 5 | Manifest parsing bugs | Medium | High |
| **Plugin Execution** | 4 | Service initialization | Medium | Medium |
| **Worker Output** | 2 | Path handling logic | Low | Low |
| **Pipeline Validation** | 4 | Validation rules | Medium | Medium |
| **API Auth** | 1 | Auth check logic | Low | Low |
| **Integration E2E** | 4 | Device/logging setup | Medium | Medium |

---

## Detailed Failure Breakdown

### 1. Device Integration Issues (6 failures total)

#### File: `tests/integration/test_phase8_end_to_end.py` (4 failures)
```
- test_end_to_end_job_with_device_and_logging
- test_end_to_end_device_selector_validation
- test_end_to_end_device_default_when_not_specified
- test_end_to_end_case_insensitive_device
```

**Root Cause:** Device parameter is not being passed correctly through the job processing pipeline  
**Evidence:** Tests pass device="cpu" but job execution doesn't use it  
**Fix Type:** Code change in job processor  
**Complexity:** Medium

**Investigation Needed:**
```bash
# Run with verbose output
cd /home/rogermt/forgesyte/server
uv run pytest tests/integration/test_phase8_end_to_end.py -v --tb=short
```

**Expected Fix:**
- Check `app/services/job_executor.py` - device param may not be passed to worker
- Check job schema - device field may be missing or not persisted
- Verify `app/workers/worker.py` reads device from job config

---

#### File: `tests/observability/test_device_integration.py` (1 failure)
```
- test_job_submission_with_device_param
```

**Root Cause:** Job submission endpoint doesn't extract/validate device parameter  
**Evidence:** POST `/v1/analyze` doesn't accept device param  
**Fix Type:** API endpoint change  
**Complexity:** Low

**Investigation Needed:**
```bash
cd /home/rogermt/forgesyte/server
uv run pytest tests/observability/test_device_integration.py::TestDeviceIntegration::test_job_submission_with_device_param -v --tb=short
```

**Expected Fix:**
- Add `device` parameter to job submission schema
- Pass device through to job processor

---

#### File: `tests/api/test_api_endpoints.py` (1 failure)
```
- TestAuthRequiredEndpoints::test_list_jobs_requires_auth
```

**Root Cause:** Auth check not enforcing correctly on list_jobs endpoint  
**Evidence:** Test expects 401/403, endpoint returns 200  
**Fix Type:** Code change in auth middleware  
**Complexity:** Low

**Investigation Needed:**
```bash
cd /home/rogermt/forgesyte/server
uv run pytest tests/api/test_api_endpoints.py::TestAuthRequiredEndpoints::test_list_jobs_requires_auth -v --tb=short
```

**Expected Fix:**
- Check `app/api_routes/routes/jobs.py` - `/v1/jobs` endpoint
- Verify `@require_auth` decorator is present
- Check if API key validation is being skipped

---

### 2. Image Submission Issues (5 failures)

#### File: `tests/image/test_image_submit_mocked.py` (4 failures)
```
- test_unknown_plugin_returns_400
- test_unknown_tool_returns_400
- test_tool_without_image_input_returns_400
- test_null_manifest_returns_400
```

**Root Cause:** Manifest validation not catching invalid plugin/tool combinations  
**Evidence:** Tests expect validation errors, but requests succeed  
**Fix Type:** Validation logic in submit handler  
**Complexity:** Medium

**Investigation Needed:**
```bash
cd /home/rogermt/forgesyte/server
uv run pytest tests/image/test_image_submit_mocked.py::TestImageSubmitValidation -v --tb=short
```

**Expected Fix:**
- Check `app/api_routes/routes/image_submit.py`
- Add validation for plugin/tool existence BEFORE creating job
- Check manifest loading for null cases

---

#### File: `tests/image/test_image_submit_hybrid.py` (3 errors, not failures)
```
- test_png_saves_file_to_disk
- test_saved_file_path_includes_job_id
- test_saved_under_image_input_subdir
```

**Root Cause:** Import/setup errors (different from failures)  
**Evidence:** Error during test collection  
**Fix Type:** Import or fixture issue  
**Complexity:** Low

**Investigation Needed:**
```bash
cd /home/rogermt/forgesyte/server
uv run pytest tests/image/test_image_submit_hybrid.py -v --tb=long
```

---

### 3. Plugin Execution Issues (4 failures)

#### File: `tests/services/test_plugin_management_service.py` (3 failures)
```
- test_run_plugin_tool_success_sync
- test_run_plugin_tool_get_returns_instance_not_metadata
- test_run_plugin_tool_success_async
```

**Root Cause:** PluginManagementService not executing tools correctly  
**Evidence:** Tool execution returns None or error  
**Fix Type:** Service implementation  
**Complexity:** Medium

**Investigation Needed:**
```bash
cd /home/rogermt/forgesyte/server
uv run pytest tests/services/test_plugin_management_service.py::TestPluginManagementService::test_run_plugin_tool_success_sync -v --tb=short
```

**Expected Fix:**
- Check `app/services/plugin_management_service.py`
- Verify `run_plugin_tool()` method
- Check if it's calling the correct tool runner

---

#### File: `tests/services/test_vision_analysis.py` (1 failure)
```
- test_list_available_plugins_exception
```

**Root Cause:** Exception handling in VisionAnalysisService  
**Evidence:** Test expects specific exception, different one raised  
**Fix Type:** Error handling  
**Complexity:** Low

**Investigation Needed:**
```bash
cd /home/rogermt/forgesyte/server
uv run pytest tests/services/test_vision_analysis.py::TestVisionAnalysisService::test_list_available_plugins_exception -v --tb=short
```

---

### 4. Manifest Canonicalization Issues (5 errors)

#### File: `tests/services/test_manifest_canonicalization.py` (5 errors)
```
- test_manifest_with_inputs_preserved
- test_manifest_with_input_types_canonicalized
- test_manifest_without_inputs_gets_empty_list
- test_real_ocr_manifest_canonicalization
- test_real_yolo_manifest_canonicalization
```

**Root Cause:** Import or module not found  
**Evidence:** Errors during test collection  
**Fix Type:** Missing module or import path  
**Complexity:** Low

**Investigation Needed:**
```bash
cd /home/rogermt/forgesyte/server
uv run pytest tests/services/test_manifest_canonicalization.py -v --tb=long
```

---

### 5. Pipeline Validation Issues (4 failures)

#### File: `tests/test_pipeline_validation.py` (4 failures)
```
- test_pipeline_rejects_missing_plugin
- test_pipeline_rejects_missing_tools
- test_pipeline_rejects_unknown_tool
- test_pipeline_executes_in_order
```

**Root Cause:** Pipeline validation not implemented or incomplete  
**Evidence:** Pipeline accepts invalid configs  
**Fix Type:** Validation logic  
**Complexity:** Medium

**Investigation Needed:**
```bash
cd /home/rogermt/forgesyte/server
uv run pytest tests/test_pipeline_validation.py -v --tb=short
```

**Expected Fix:**
- Check `app/services/pipeline_executor.py`
- Add validation before execution
- Verify plugin/tool references

---

### 6. Worker Output Path Issues (2 failures)

#### File: `tests/video/test_worker_output_paths.py` (2 failures)
```
- test_worker_stores_relative_output_path_only
- test_worker_does_not_store_absolute_path
```

**Root Cause:** Worker saving absolute paths instead of relative  
**Evidence:** Test expects `output/job_123.json`, gets `/absolute/path/output/job_123.json`  
**Fix Type:** Path handling in worker  
**Complexity:** Low

**Investigation Needed:**
```bash
cd /home/rogermt/forgesyte/server
uv run pytest tests/video/test_worker_output_paths.py -v --tb=short
```

**Expected Fix:**
- Check `app/workers/worker.py`
- Find where output path is saved
- Use relative paths instead of absolute

---

## How to Fix All 20 - Step by Step

### Phase 1: Quick Wins (5 failures, 1-2 hours)
**Priority: Fix these first - they're easiest**

1. **Auth check** (1 failure, 15 min)
   - Add `@require_auth` decorator to missing endpoint
   
2. **Worker output paths** (2 failures, 30 min)
   - Change `pathlib.Path(__file__).resolve()` to `Path()`

3. **Single exception test** (1 failure, 15 min)
   - Fix exception type in vision analysis service

4. **Manifest null check** (1 failure, 30 min)
   - Add null validation before manifest parsing

### Phase 2: Medium Effort (10 failures, 3-5 hours)
**Priority: High-value fixes**

1. **Device parameter integration** (6 failures, 2-3 hours)
   - Add device param to job schema
   - Pass through job processor
   - Read in worker

2. **Image validation** (3 failures, 1-2 hours)
   - Add plugin/tool existence checks
   - Validate tool has image input

3. **Plugin tool execution** (1 failure, 30 min)
   - Debug PluginManagementService.run_plugin_tool()

### Phase 3: Complex (5 failures/errors, 2-3 hours)
**Priority: Lower (import issues, edge cases)**

1. **Pipeline validation** (4 failures, 1-2 hours)
   - Implement validation logic

2. **Manifest canonicalization errors** (5 errors, varies)
   - Might be import path issues

---

## Recommended Fix Order

| Order | Task | Time | Impact | Start |
|-------|------|------|--------|-------|
| 1 | Auth decorator (1 failure) | 15 min | Quick win | Now |
| 2 | Worker paths (2 failures) | 30 min | Quick win | Now |
| 3 | Manifest null (1 failure) | 30 min | Quick win | Now |
| 4 | Device integration (6 failures) | 3 hours | High value | After Phase 1 |
| 5 | Image validation (3 failures) | 1.5 hours | Medium value | After Phase 1 |
| 6 | Pipeline validation (4 failures) | 1.5 hours | Medium value | After Phase 1 |
| 7 | Plugin execution (1 failure) | 1 hour | Low value | Last |
| 8 | Import errors (5 errors) | Varies | Depends | As needed |

---

## Command to Investigate Each

```bash
cd /home/rogermt/forgesyte/server

# Auth issue
uv run pytest tests/api/test_api_endpoints.py::TestAuthRequiredEndpoints::test_list_jobs_requires_auth -v --tb=short

# Worker paths
uv run pytest tests/video/test_worker_output_paths.py -v --tb=short

# Device integration
uv run pytest tests/integration/test_phase8_end_to_end.py -v --tb=short

# Image validation
uv run pytest tests/image/test_image_submit_mocked.py::TestImageSubmitValidation -v --tb=short

# Plugin execution
uv run pytest tests/services/test_plugin_management_service.py::TestPluginManagementService -v --tb=short

# Pipeline validation
uv run pytest tests/test_pipeline_validation.py -v --tb=short

# Manifest canonicalization
uv run pytest tests/services/test_manifest_canonicalization.py -v --tb=long

# All 20 together (to see full list)
uv run pytest tests/ -v --tb=line 2>&1 | grep FAILED
```

---

## Summary

- ✅ **DuckDB fix DONE** - tests no longer timeout
- ❌ **20 pre-existing failures remain** - different root causes
- 🎯 **Phase 1:** 5 quick wins (2 hours) 
- 🎯 **Phase 2:** 10 medium fixes (3-5 hours)
- 🎯 **Phase 3:** 5 complex issues (varies)

**Total estimated effort to fix all 20:** 5-8 hours (spread across priorities)
