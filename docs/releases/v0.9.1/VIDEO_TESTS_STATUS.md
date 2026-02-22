# Video Integration Tests - Restoration Status

**Created:** 2026-02-18  
**Status:** ✅ RESTORED  
**Location:** `/server/app/tests/video/`

---

## 📋 Summary

The full Phase-15 video integration test suite has been successfully restored and is available at `/server/app/tests/video/`. These tests were originally removed during Phase 17 and have been fully restored and updated for v0.9.1.

---

## 📂 Directory Structure

```
server/app/tests/video/
├── __init__.py
├── test_integration_video_processing.py      # Integration tests (12 scenarios)
├── test_router_registration.py                # Router registration tests
├── test_schema_regression.py                 # Schema regression tests
├── test_stress_and_fuzz.py                   # Stress and fuzz tests
├── test_video_golden_snapshot.py             # Golden snapshot tests
├── test_video_router_registered.py           # Router registration validation
├── test_video_service_unit.py                # Unit tests for video service
├── fakes/
│   ├── __init__.py
│   ├── corrupt_mp4_generator.py              # MP4 generator for testing
│   └── mock_dag_service.py                   # Mock DAG service
├── fuzz/
│   ├── __init__.py
│   └── test_video_service_mp4_fuzz.py        # Fuzz tests for corrupt MP4s
├── golden/
│   ├── __init__.py
│   └── golden_output.json                    # Golden snapshot reference
└── stress/
    ├── __init__.py
    └── test_video_service_1000_frames.py     # Stress test for 1000 frames
```

---

## 🧪 Test Coverage

### 1. Integration Tests (`test_integration_video_processing.py`)

**Covers 12 scenarios:**
- ✅ Scenario 1: 200 success
- ✅ Scenario 2: 400 invalid file type
- ✅ Scenario 3: 404 invalid pipeline
- ✅ Scenario 4: 400 empty file
- ✅ Scenario 5: 400 corrupted MP4
- ✅ Scenario 6: 422 missing fields
- ✅ Parameter validation: frame_stride, max_frames
- ✅ Response schema validation: results field, results is array, results have frame_index + result

**Test Classes:**
- `TestVideoEndpointIntegration` - Endpoint validation (no DAG execution required)
- `TestVideoEndpointResponseSchema` - Response schema matches frozen spec
- `TestVideoEndpointQueryParams` - Query parameter validation

---

### 2. Router Registration Tests (`test_router_registration.py`)

**Verifies:**
- ✅ Router is properly registered in FastAPI app
- ✅ Endpoint schema is correct
- ✅ Request/response contracts match frozen spec
- ✅ Video router module imports correctly
- ✅ Router has the /process endpoint
- ✅ Schemas are exported (VideoProcessingRequest, VideoProcessingResponse, FrameResult)

**Test Classes:**
- `TestVideoRouterEndpointRegistration` - Endpoint registration in OpenAPI spec
- `TestVideoRouterImports` - Module imports and instantiation

---

### 3. Schema Regression Tests (`test_schema_regression.py`)

**Verifies:**
- ✅ Frozen response schema never changes
- ✅ Request schema validation
- ✅ Field types and required fields
- ✅ Response schema matches golden snapshot

**Golden Snapshot:**
```json
{
  "type": "object",
  "properties": {
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "frame_index": {"type": "integer"},
          "result": {"type": "object"}
        },
        "required": ["frame_index", "result"]
      }
    }
  },
  "required": ["results"]
}
```

---

### 4. Unit Tests (`test_video_service_unit.py`)

**Validates:**
- ✅ VideoFilePipelineService calls DagPipelineService correctly
- ✅ Service interactions are correct
- ✅ Mock DAG service works as expected

---

### 5. Fuzz Tests (`fuzz/test_video_service_mp4_fuzz.py`)

**Ensures:**
- ✅ Corrupt MP4s do not crash the service
- ✅ Service handles invalid inputs gracefully
- ✅ Error handling is robust

---

### 6. Stress Tests (`stress/test_video_service_1000_frames.py`)

**Validates:**
- ✅ Service handles 1000 frames
- ✅ Performance under heavy load
- ✅ Stability with large inputs

---

### 7. Golden Snapshot Tests (`test_video_golden_snapshot.py`)

**Compares:**
- ✅ Output to known-good reference
- ✅ Schema regression
- ✅ Output format consistency

---

## 🔄 Migration from Phase-15 to v0.9.1

### Updated References

| Old (Phase-15) | New (v0.9.1) |
|----------------|--------------|
| `VideoService` | `VideoFilePipelineService` |
| `PipelineExecutor` | `DagPipelineService` |
| `pipeline_id="video_ocr"` | `"ocr_only"` or `"yolo_ocr"` |
| `video_router` | `video_routes` |
| `run_pipeline(...)` | `run_pipeline(pipeline_id, frames)` |
| `generate_mp4()` | `generate_valid_mp4()` |

### Import Paths

All tests use the updated v0.9.1 import structure:
```python
from server.services.video_file_pipeline_service import VideoFilePipelineService
from server.tests.video.fakes.corrupt_mp4_generator import generate_valid_mp4
```

---

## 🚀 Running the Test Suite

### Run All Video Tests
```bash
cd server
uv run pytest app/tests/video -v
```

### Run Specific Test File
```bash
cd server
uv run pytest app/tests/video/test_integration_video_processing.py -v
```

### Run Specific Test Class
```bash
cd server
uv run pytest app/tests/video/test_integration_video_processing.py::TestVideoEndpointIntegration -v
```

### Run Specific Test Method
```bash
cd server
uv run pytest app/tests/video/test_integration_video_processing.py::TestVideoEndpointIntegration::test_scenario_1_upload_success -v
```

### Run with Coverage
```bash
cd server
uv run pytest app/tests/video --cov=app --cov-report=term-missing
```

---

## 📊 Test Results

### Expected Results

All tests should pass with the v0.9.1 backend:

```
test_integration_video_processing.py::TestVideoEndpointIntegration::test_scenario_1_upload_success PASSED
test_integration_video_processing.py::TestVideoEndpointIntegration::test_scenario_2_invalid_file_type PASSED
test_integration_video_processing.py::TestVideoEndpointIntegration::test_scenario_3_invalid_pipeline_id PASSED
test_integration_video_processing.py::TestVideoEndpointIntegration::test_scenario_4_empty_file PASSED
test_integration_video_processing.py::TestVideoEndpointIntegration::test_scenario_5_corrupted_mp4 PASSED
test_integration_video_processing.py::TestVideoEndpointIntegration::test_scenario_6_missing_form_fields PASSED
test_router_registration.py::TestVideoRouterEndpointRegistration::test_video_endpoint_in_openapi PASSED
test_schema_regression.py::TestSchemaRegression::test_response_schema_matches_golden PASSED
test_video_service_unit.py::test_video_service_calls_dag PASSED
fuzz/test_video_service_mp4_fuzz.py::test_video_service_mp4_fuzz PASSED
stress/test_video_service_1000_frames.py::test_video_service_1000_frames PASSED
test_video_golden_snapshot.py::test_video_golden_snapshot PASSED
```

---

## 🛠️ Test Utilities

### MP4 Generator (`fakes/corrupt_mp4_generator.py`)

```python
def generate_valid_mp4(tmp_path: Path) -> Path:
    """Generates a tiny valid MP4 for testing."""
    p = tmp_path / "test.mp4"
    p.write_bytes(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42mp41")
    return p

def generate_corrupt_mp4(tmp_path: Path) -> Path:
    """Generates a corrupt MP4 for fuzz tests."""
    p = tmp_path / "corrupt.mp4"
    p.write_bytes(b"NOT_AN_MP4")
    return p
```

### Mock DAG Service (`fakes/mock_dag_service.py`)

```python
class MockDagService:
    """Fake DAG service for unit tests."""
    def __init__(self):
        self.called = False

    def run_pipeline(self, pipeline_id, frames):
        self.called = True
        return {"frames": frames, "text": "mock", "detections": []}
```

---

## 📝 Updating Golden Snapshots

If the output format changes intentionally:

1. Update `golden/golden_output.json`
2. Update schema tests
3. Document the change in the release notes

---

## 🎯 Test Philosophy

This suite enforces:
- ✅ Stability
- ✅ Backward compatibility
- ✅ Architectural integrity
- ✅ Contributor discipline

It is a core part of the v1.0.0 quality bar.

---

## 🔗 References

- `/docs/releases/v0.9.1/VIDEO_INT_TESTS_RESTORED.md` - Original restoration documentation
- `/docs/releases/v0.9.1/TDD_IMPLEMENTATION_PLAN.md` - TDD implementation plan
- `/docs/releases/v0.9.1/DOCUMENTS.md` - Complete v0.9.1 documentation
- `/AGENTS.md` - Agent commands and conventions

---

**Last Updated:** 2026-02-18  
**Status:** ✅ All tests restored and ready for use