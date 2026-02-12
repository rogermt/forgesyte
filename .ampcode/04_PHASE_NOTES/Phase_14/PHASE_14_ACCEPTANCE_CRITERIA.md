# ⭐ PHASE 14 — ACCEPTANCE CRITERIA

## What Success Looks Like

Phase 14 is complete when **all criteria below are met**.

---

## 1. DAG Validation

### 1.1 Reject Cycles

**Test**: Invalid pipeline with cycle

```json
{
  "nodes": ["n1", "n2"],
  "edges": [
    { "from_node": "n1", "to_node": "n2" },
    { "from_node": "n2", "to_node": "n1" }
  ]
}
```

**Expected**: Error with message "contains cycle"

**Status**: ✅ PASS / ❌ FAIL

---

### 1.2 Reject Unknown Plugins

**Test**: Pipeline references non-existent plugin

```json
{
  "nodes": [
    { "id": "n1", "plugin_id": "nonexistent-plugin", "tool_id": "x" }
  ]
}
```

**Expected**: Error "plugin not found"

**Status**: ✅ PASS / ❌ FAIL

---

### 1.3 Reject Unknown Tools

**Test**: Pipeline references non-existent tool

```json
{
  "nodes": [
    { "id": "n1", "plugin_id": "ocr", "tool_id": "nonexistent-tool" }
  ]
}
```

**Expected**: Error "tool not found"

**Status**: ✅ PASS / ❌ FAIL

---

### 1.4 Reject Type Mismatches

**Test**: Pipeline edges with incompatible types

```
Node A outputs: ["detections"]
Node B inputs: ["heatmap"]
Edge: A → B
```

**Expected**: Error "type mismatch"

**Status**: ✅ PASS / ❌ FAIL

---

### 1.5 Reject Invalid Entry Nodes

**Test**: Entry node doesn't exist

```json
{
  "entry_nodes": ["nonexistent"]
}
```

**Expected**: Error "entry node not found"

**Status**: ✅ PASS / ❌ FAIL

---

### 1.6 Reject Invalid Output Nodes

**Test**: Output node doesn't exist

```json
{
  "output_nodes": ["nonexistent"]
}
```

**Expected**: Error "output node not found"

**Status**: ✅ PASS / ❌ FAIL

---

### 1.7 Reject Unreachable Nodes

**Test**: Pipeline with disconnected node

```
n1 → n2
n3 (not connected)
```

**Expected**: Error "node n3 is unreachable"

**Status**: ✅ PASS / ❌ FAIL

---

### 1.8 Accept Valid DAGs

**Test**: Multiple valid pipeline structures

- Linear: A → B → C
- Branching: A → {B, C} → D
- Merging: {A, B} → C

**Expected**: All validate successfully

**Status**: ✅ PASS / ❌ FAIL

---

## 2. DAG Execution

### 2.1 Execute in Topological Order

**Test**: Monitor execution order

```
n1 (no deps)
  ↓
{n2, n3} (depend on n1)
  ↓
n4 (depends on n2, n3)
```

**Expected**: Execution order is [n1, n2, n3, n4] (n2/n3 can be parallel)

**Status**: ✅ PASS / ❌ FAIL

---

### 2.2 Merge Predecessor Outputs

**Test**: Node with multiple inputs

```
n1 → {n2, n3} → n4
```

Payload for n4 should be:
```python
{
    **initial_payload,
    **n2_output,
    **n3_output
}
```

**Expected**: Merged payload contains all outputs

**Status**: ✅ PASS / ❌ FAIL

---

### 2.3 Execute Cross-Plugin Nodes

**Test**: Pipeline with tools from different plugins

```
YOLO.detect_players → ReID.track_ids
```

**Expected**: 
- YOLO runs first, outputs detections
- ReID receives detections, runs second

**Status**: ✅ PASS / ❌ FAIL

---

### 2.4 Return Output Node Results

**Test**: Multiple output nodes

```
n1 → {n2, n3}
output_nodes: ["n2", "n3"]
```

**Expected**: Final result contains outputs from both n2 and n3

**Status**: ✅ PASS / ❌ FAIL

---

### 2.5 Log Each Node Execution

**Test**: Inspect execution logs

**Expected**: Each node execution logs:
- pipeline_id
- node_id
- plugin_id
- tool_id
- execution_time_ms
- status (success/error)

**Status**: ✅ PASS / ❌ FAIL

---

### 2.6 Handle Execution Errors

**Test**: Node fails during execution

**Expected**: 
- Execution stops
- Error is logged
- Error is returned to user
- Pipeline doesn't crash

**Status**: ✅ PASS / ❌ FAIL

---

## 3. Registry

### 3.1 List Pipelines

**Test**: GET `/pipelines/list`

**Expected**: 
- Returns JSON array of pipelines
- Each pipeline has id, name, description

**Status**: ✅ PASS / ❌ FAIL

---

### 3.2 Fetch Pipeline by ID

**Test**: GET `/pipelines/{id}/info`

**Expected**:
- Returns pipeline metadata
- Includes nodes, edges, entry/output nodes
- Does not require full execution

**Status**: ✅ PASS / ❌ FAIL

---

### 3.3 Run Pipeline via REST

**Test**: POST `/pipelines/{id}/run`

**Expected**:
- Accepts JSON payload
- Returns execution result
- Includes output data
- Includes execution_time_ms

**Status**: ✅ PASS / ❌ FAIL

---

### 3.4 Run Pipeline via WebSocket

**Test**: Send pipeline execution via WS

```json
{
  "type": "frame",
  "pipeline_id": "player_tracking_v1",
  "frame_id": "frame_001",
  "image": "base64_data"
}
```

**Expected**:
- Accepts pipeline_id parameter
- Executes pipeline
- Returns result on same WebSocket

**Status**: ✅ PASS / ❌ FAIL

---

## 4. Logging

### 4.1 Pipeline Execution Log

**Test**: Check logs for pipeline execution

**Expected**: Log entry contains:
```json
{
  "level": "INFO",
  "timestamp": "2026-02-12T10:30:45Z",
  "pipeline_id": "player_tracking_v1",
  "node_id": "detect",
  "plugin_id": "forgesyte-yolo-tracker",
  "tool_id": "detect_players",
  "status": "success",
  "execution_time_ms": 125.5
}
```

**Status**: ✅ PASS / ❌ FAIL

---

### 4.2 Validation Error Logging

**Test**: Invalid pipeline attempted

**Expected**: Log includes:
- Pipeline ID attempted
- Specific validation error
- Why it failed

**Status**: ✅ PASS / ❌ FAIL

---

## 5. UI

### 5.1 Pipeline Selector Displays

**Test**: Load web-ui

**Expected**:
- Dropdown/selector showing all pipelines
- User can select one
- Selected pipeline is highlighted

**Status**: ✅ PASS / ❌ FAIL

---

### 5.2 Pipeline Metadata Shows

**Test**: User hovers over pipeline

**Expected**:
- Tooltip shows pipeline description
- Shows number of nodes
- Shows tags/capabilities

**Status**: ✅ PASS / ❌ FAIL

---

### 5.3 Pipeline Execution Works

**Test**: User selects pipeline, uploads image, clicks run

**Expected**:
- Request sent with `pipeline_id`
- UI shows loading state
- Results display correctly
- Execution time shown

**Status**: ✅ PASS / ❌ FAIL

---

### 5.4 Error Handling in UI

**Test**: Invalid pipeline or execution error

**Expected**:
- Error message displayed
- User-friendly explanation
- No crash

**Status**: ✅ PASS / ❌ FAIL

---

## 6. Type Safety

### 6.1 TypeScript Strict Mode

**Test**: Run `npm run type-check`

**Expected**: Zero type errors

**Status**: ✅ PASS / ❌ FAIL

---

### 6.2 Python Type Checking

**Test**: Run `mypy app/`

**Expected**: Zero type errors in Phase 14 code

**Status**: ✅ PASS / ❌ FAIL

---

## 7. Testing

### 7.1 Unit Tests Pass

**Test**: Run `pytest tests/pipelines/`

**Expected**: All tests pass

**Status**: ✅ PASS / ❌ FAIL

---

### 7.2 Integration Tests Pass

**Test**: Run `pytest tests/integration/test_pipeline_*.py`

**Expected**: All tests pass

**Status**: ✅ PASS / ❌ FAIL

---

### 7.3 Coverage

**Test**: Check coverage

**Expected**: > 85% for Phase 14 code

**Status**: ✅ PASS / ❌ FAIL

---

## 8. Quality Checks

### 8.1 Linting Passes

**Test**: Run `ruff check app/ tests/`

**Expected**: No linting errors

**Status**: ✅ PASS / ❌ FAIL

---

### 8.2 Formatting Passes

**Test**: Run `black --check app/ tests/`

**Expected**: All files correctly formatted

**Status**: ✅ PASS / ❌ FAIL

---

### 8.3 Pre-commit Passes

**Test**: Run `pre-commit run --all-files`

**Expected**: All hooks pass

**Status**: ✅ PASS / ❌ FAIL

---

## 9. Backward Compatibility

### 9.1 Phase 13 Still Works

**Test**: Run single tool (no pipeline)

**Expected**: Single-tool execution still works

**Status**: ✅ PASS / ❌ FAIL

---

### 9.2 All Phase 13 Tests Pass

**Test**: Run full test suite

**Expected**: 1200+ tests pass (including Phase 13 tests)

**Status**: ✅ PASS / ❌ FAIL

---

## 10. Documentation

### 10.1 Overview Document

**Status**: ✅ DONE / ❌ MISSING

---

### 10.2 Architecture Document

**Status**: ✅ DONE / ❌ MISSING

---

### 10.3 Developer Guide

**Status**: ✅ DONE / ❌ MISSING

---

### 10.4 Governance Rules

**Status**: ✅ DONE / ❌ MISSING

---

### 10.5 Example Pipelines

**Status**: ✅ DONE / ❌ MISSING

---

## Final Checklist

- [ ] All validation tests pass (1-8)
- [ ] All execution tests pass (2.1-2.6)
- [ ] All registry tests pass (3.1-3.4)
- [ ] All logging tests pass (4.1-4.2)
- [ ] All UI tests pass (5.1-5.4)
- [ ] Type checking passes (6.1-6.2)
- [ ] Unit tests pass (7.1)
- [ ] Integration tests pass (7.2)
- [ ] Coverage > 85% (7.3)
- [ ] Linting passes (8.1)
- [ ] Formatting passes (8.2)
- [ ] Pre-commit passes (8.3)
- [ ] Phase 13 still works (9.1)
- [ ] All tests pass (9.2)
- [ ] Documentation complete (10.1-10.5)

**When all items are checked**: Phase 14 is COMPLETE ✅
