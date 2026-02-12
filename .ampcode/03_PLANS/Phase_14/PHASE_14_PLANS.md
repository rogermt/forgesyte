# ⭐ PHASE 14 — PLANS (Single Source of Truth)

**Cross‑Plugin DAG Pipelines with Typed Edges**

---

## 🎯 Vision

Transform ForgeSyte from **linear, single-plugin pipelines** to **graph-based, cross-plugin workflows with explicit type contracts**.

This is the moment the system becomes a **workflow engine**, not just a plugin runner.

---

## 📋 What Changes

### Before (Phase 13)
```
User Input → OCR Plugin (detect_text) → Result
User Input → YOLO Plugin (detect_players) → Result
```
Each plugin runs independently. No composition.

### After (Phase 14)
```
Video Frame
    ↓
YOLO.detect_players
    ↓
ReID.track_ids
    ↓
Viz.render_overlay
    ↓
Output Frame
```
Plugins work **together** in a graph.

---

## 🏗️ Key Capabilities

| Capability | Description |
|------------|-------------|
| **DAG Pipelines** | Workflows are directed acyclic graphs |
| **Tool Metadata** | Each tool declares inputs/outputs/capabilities |
| **Pipeline Registry** | Named pipelines stored server-side |
| **Type Validation** | Explicit type contracts on edges |
| **Execution Engine** | Topological sort → Execute → Merge → Return |

---

## 📅 10-Commit Migration Plan

### COMMIT 1: Add Pipeline Graph Models
**Goal**: Define core data structures

**Changes**:
- Create `app/models/pipeline_graph_models.py`
- Define `PipelineNode`, `PipelineEdge`, `Pipeline`
- Define `ToolMetadata`, `PipelineValidationResult`
- Add Pydantic validation

**Files**:
- ✨ `app/models/pipeline_graph_models.py`

**Tests**:
- `tests/pipelines/test_pipeline_models.py`

**Acceptance**:
```python
node = PipelineNode(id="n1", plugin_id="ocr", tool_id="detect")
assert node.plugin_id == "ocr"
```

---

### COMMIT 2: Add Tool Capability Metadata
**Goal**: Allow plugins to declare input/output types

**Changes**:
- Add `input_types`, `output_types`, `capabilities` to plugin manifests
- Update plugin registry to read metadata
- Document in developer guide

**Files**:
- 🔧 `app/plugins/plugin_manager.py`
- 🔧 `plugins/*/manifest.json`
- 📝 `docs/phases/PHASE_14_DEVELOPER_GUIDE.md`

**Example Manifest**:
```json
{
  "tools": {
    "detect_players": {
      "input_types": ["video_frame"],
      "output_types": ["detections"],
      "capabilities": ["player_detection"]
    }
  }
}
```

**Tests**:
- `tests/pipelines/test_tool_metadata.py`

---

### COMMIT 3: Add Pipeline Registry Service
**Goal**: Load and manage named pipelines

**Changes**:
- Create `app/services/pipeline_registry_service.py`
- Load all `.json` files from `app/pipelines/`
- Implement `list()`, `get()`, `get_info()`
- Create `app/pipelines/` directory
- Add example pipelines

**Files**:
- ✨ `app/services/pipeline_registry_service.py`
- ✨ `app/pipelines/` (directory)
- ✨ `app/pipelines/player_tracking_v1.json`
- ✨ `app/pipelines/ball_tracking_v1.json`

**Tests**:
- `tests/pipelines/test_pipeline_registry.py`

**Acceptance**:
```python
registry = PipelineRegistry("app/pipelines")
pipeline = registry.get("player_tracking_v1")
assert pipeline.id == "player_tracking_v1"
```

---

### COMMIT 4: Add DAG Pipeline Service
**Goal**: Core pipeline execution engine

**Changes**:
- Create `app/services/dag_pipeline_service.py`
- Implement `validate()` method
- Implement `execute()` method (async)
- Add topological sort algorithm
- Add cycle detection

**Files**:
- ✨ `app/services/dag_pipeline_service.py`

**Core Methods**:
```python
class DAGPipelineService:
    def validate(self, pipeline: Pipeline) -> PipelineValidationResult
    async def execute(self, pipeline, payload, plugin_manager) -> PipelineExecutionResult
```

**Tests**:
- `tests/pipelines/test_dag_pipeline.py`

---

### COMMIT 5: Add Topological Sort & DAG Validation
**Goal**: Ensure deterministic execution order

**Changes**:
- Implement topological sort (Kahn's algorithm)
- Implement cycle detection (DFS)
- Add validation for entry/output nodes
- Add validation for reachability

**Files**:
- 🔧 `app/services/dag_pipeline_service.py`

**Validation Rules**:
1. Graph is acyclic
2. All nodes exist
3. All entry nodes exist and have no predecessors
4. All output nodes exist and are reachable
5. No unreachable nodes

**Tests**:
- `tests/pipelines/test_dag_validation.py`

---

### COMMIT 6: Add Type Compatibility Validation
**Goal**: Ensure output/input types match

**Changes**:
- Implement type intersection algorithm
- Add validation for each edge
- Report type mismatches clearly

**Files**:
- ✨ `app/services/type_validator.py`
- 🔧 `app/services/dag_pipeline_service.py`

**Validation**:
```python
for edge in pipeline.edges:
    from_outputs = node[edge.from_node].output_types
    to_inputs = node[edge.to_node].input_types
    if not (from_outputs & to_inputs):
        raise TypeError(f"Type mismatch: {edge.from_node} → {edge.to_node}")
```

**Tests**:
- `tests/pipelines/test_type_validation.py`

---

### COMMIT 7: Add REST Pipeline Endpoints
**Goal**: Expose pipelines via HTTP API

**Changes**:
- Create `app/routes/routes_pipelines.py`
- Implement `/pipelines/list`
- Implement `/pipelines/{id}/info`
- Implement `/pipelines/{id}/run`
- Implement `/pipelines/validate`
- Mount routes in `app/main.py`

**Files**:
- ✨ `app/routes/routes_pipelines.py`
- 🔧 `app/main.py`

**Endpoints**:
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/pipelines/list` | List all pipelines |
| GET | `/pipelines/{id}/info` | Get pipeline metadata |
| POST | `/pipelines/{id}/run` | Execute pipeline |
| POST | `/pipelines/validate` | Validate pipeline spec |

**Tests**:
- `tests/pipelines/test_pipeline_endpoints.py`

---

### COMMIT 8: Add UI Pipeline Selector
**Goal**: User selects which pipeline to run

**Changes**:
- Create `web-ui/src/types/pipeline_graph.ts`
- Create `web-ui/src/api/pipelines.ts`
- Create `web-ui/src/components/VideoTracker/PipelineSelector.tsx`
- Integrate with VideoTracker component

**Files**:
- ✨ `web-ui/src/types/pipeline_graph.ts`
- ✨ `web-ui/src/api/pipelines.ts`
- ✨ `web-ui/src/components/VideoTracker/PipelineSelector.tsx`
- 🔧 `web-ui/src/components/VideoTracker/VideoTracker.tsx`

**Tests**:
- `web-ui/src/tests/PipelineSelector.test.tsx`

---

### COMMIT 9: Add Acceptance Tests
**Goal**: E2E tests for full workflow

**Changes**:
- Create `tests/pipelines/test_pipeline_integration.py`
- Test full workflow: validate → execute → verify output
- Test with real plugins
- Test error cases

**Files**:
- ✨ `tests/pipelines/test_pipeline_integration.py`
- ✨ `tests/integration/test_pipeline_with_plugins.py`

**Test Cases**:
```python
@pytest.mark.asyncio
async def test_e2e_player_tracking_pipeline():
    pipeline = registry.get("player_tracking_v1")
    validation = service.validate(pipeline)
    assert validation.valid
    result = await service.execute(pipeline, image_bytes, plugin_manager)
    assert result.status == "success"
    assert "detections" in result.output
```

---

### COMMIT 10: Remove Single-Plugin Assumptions
**Goal**: Finalize Phase 14 migration

**Changes**:
- Update all code to use Phase 14 patterns
- Remove any remaining fallback to single-plugin
- Ensure all tests use explicit pipelines
- Update documentation

**Files Modified**:
- 🔧 Any files still assuming single-plugin execution
- 🔧 Test files (update patterns)

**Verification**:
- ✅ All 1100+ tests pass
- ✅ Type checking passes
- ✅ Linting passes
- ✅ Pre-commit hooks pass
- ✅ No regressions

---

## ⏱️ Timeline

| Commit | Task | Est. Time | Cumulative |
|--------|------|-----------|------------|
| 1 | Models | 2h | 2h |
| 2 | Metadata | 2h | 4h |
| 3 | Registry | 3h | 7h |
| 4 | DAG Engine | 4h | 11h |
| 5 | Validation | 3h | 14h |
| 6 | Type Checking | 2h | 16h |
| 7 | REST API | 3h | 19h |
| 8 | UI | 4h | 23h |
| 9 | Tests | 3h | 26h |
| 10 | Cleanup | 2h | 28h |

**Total**: ~28 hours of development

---

## ✅ Success Metrics

- ✅ All 10 commits merged to main
- ✅ 1200+ tests passing
- ✅ Zero type errors
- ✅ Zero linting errors
- ✅ All pre-commit hooks pass
- ✅ Documentation complete
- ✅ UI functional
- ✅ No regressions vs Phase 13

---

## 🔄 Rollback Plan

If any commit fails:
1. Revert to previous commit
2. Identify issue
3. Fix and re-test
4. Retry commit

Each commit is self-contained, so rollback is clean.

---

## 🚀 Next Phase

Once Phase 14 is locked:
- Phase 15: Job queuing for pipelines
- Phase 16: Pipeline performance metrics
- Phase 17: Pipeline versioning and history

---

## 📖 References

- **Overview**: `.ampcode/04_PHASE_NOTES/Phase_14/PHASE_14_OVERVIEW.md`
- **Architecture**: `.ampcode/04_PHASE_NOTES/Phase_14/PHASE_14_ARCHITECTURE.md`
- **Developer Guide**: `.ampcode/04_PHASE_NOTES/Phase_14/PHASE_14_DEVELOPER_GUIDE.md`
- **Governance Rules**: `.ampcode/04_PHASE_NOTES/Phase_14/PHASE_14_GOVERNANCE_RULES.md`
- **Acceptance Criteria**: `.ampcode/04_PHASE_NOTES/Phase_14/PHASE_14_ACCEPTANCE_CRITERIA.md`