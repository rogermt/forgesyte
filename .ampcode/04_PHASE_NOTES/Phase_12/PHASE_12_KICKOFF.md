# Phase 12 Kickoff – Multi-Plugin Orchestration

**Opening the door to composable, chainable plugin workflows.**

Phase 12 is where your plugin system transforms from **single-plugin-per-job** to **multi-plugin-pipelines**.

---

## Phase 12 Vision

**One job can orchestrate multiple plugins in sequence with realtime updates, error isolation, and deterministic output.**

Example:

```json
{
  "job_id": "job-123",
  "pipeline": [
    {
      "plugin": "forgesyte-yolo-tracker",
      "tool": "detect_players",
      "config": { "device": "cuda", "confidence": 0.25 }
    },
    {
      "plugin": "pose-estimator",
      "tool": "estimate_poses",
      "config": { "model": "light" }
    },
    {
      "plugin": "classifier",
      "tool": "classify_actions",
      "config": {}
    }
  ]
}
```

**Pipeline executes:**

```
Input Frame
  ↓
[Stage 1] VideoTracker: detect_players()
  ↓ (output: detected_players)
[Stage 2] PoseEstimator: estimate_poses()
  ↓ (output: poses)
[Stage 3] Classifier: classify_actions()
  ↓ (output: actions)
Final Result: { players, poses, actions }
```

Realtime updates at each stage. If any stage fails, error is isolated and reported.

---

## Core Deliverables

### 1. Pipeline Definition Model

**What:** JSON schema describing plugin sequences

**Location:** `server/app/models/pipeline.py`

**Structure:**

```python
from pydantic import BaseModel

class PipelineStage(BaseModel):
    plugin: str  # Plugin name
    tool: str    # Tool name
    config: dict = {}  # Tool configuration

class PipelineDefinition(BaseModel):
    stages: list[PipelineStage]
    timeout_seconds: float = 300.0
    description: str = ""
```

**Example:**

```python
pipeline = PipelineDefinition(
    stages=[
        PipelineStage(plugin="videotracker", tool="detect_players"),
        PipelineStage(plugin="pose", tool="estimate_poses"),
    ],
    timeout_seconds=60.0,
)
```

---

### 2. Pipeline Executor

**What:** Runs plugins in sequence, passes output through stages

**Location:** `server/app/plugins/orchestration/pipeline_executor.py`

**Signature:**

```python
class PipelineExecutor:
    def execute(
        self,
        pipeline: PipelineDefinition,
        input_data: dict,
        job_id: str,
    ) -> dict:
        """
        Execute pipeline stages in order.
        
        Args:
            pipeline: Pipeline definition
            input_data: Input to first stage
            job_id: For tracking
        
        Returns:
            { "ok": True, "result": {...}, "stages_executed": 3 }
            or
            { "ok": False, "error": "...", "stage_failed": 2 }
        """
```

**Key behaviors:**

- Run each stage in sandbox (Phase 11 safety)
- Pass output of stage N to input of stage N+1
- Update lifecycle per plugin per stage
- Emit realtime messages on stage completion
- Stop on first failure
- Return partial results on error

---

### 3. Realtime Pipeline Messages

**What:** WebSocket messages for realtime pipeline visibility

**Format:**

```json
{
  "type": "pipeline_stage_start",
  "job_id": "job-123",
  "stage_index": 0,
  "plugin": "videotracker",
  "tool": "detect_players",
  "timestamp": "2026-02-15T10:30:00Z"
}

{
  "type": "pipeline_stage_end",
  "job_id": "job-123",
  "stage_index": 0,
  "plugin": "videotracker",
  "duration_ms": 1250,
  "ok": true,
  "result_size_bytes": 45230,
  "timestamp": "2026-02-15T10:30:01.25Z"
}

{
  "type": "pipeline_error",
  "job_id": "job-123",
  "stage_index": 1,
  "plugin": "pose",
  "error": "Memory error during inference",
  "error_type": "RuntimeError",
  "timestamp": "2026-02-15T10:30:02Z"
}

{
  "type": "pipeline_progress",
  "job_id": "job-123",
  "stages_total": 3,
  "stages_completed": 2,
  "percent": 67,
  "timestamp": "2026-02-15T10:30:02.5Z"
}
```

---

### 4. Pipeline Health Reporting

**What:** API endpoints for pipeline observability

**Endpoints:**

```
GET /v1/pipelines
  → List all pipeline definitions (saved templates)
  → Returns: [{ id, name, stages, created_at }, ...]

GET /v1/pipelines/{id}
  → Get pipeline details
  → Returns: { id, name, stages, last_used, success_rate, ... }

GET /v1/jobs/{job_id}/pipeline
  → Get pipeline execution state for a job
  → Returns: { job_id, pipeline, stages_executed, current_stage, status, ... }
```

---

### 5. Pipeline RED Tests

**What:** Test contract for multi-plugin orchestration

**Test files:**

```
server/tests/test_pipeline_orchestration/
├── test_pipeline_definition.py
├── test_pipeline_executor_success.py
├── test_pipeline_executor_failure.py
├── test_pipeline_realtime_messages.py
├── test_pipeline_partial_results.py
└── test_pipeline_timeout.py
```

**Example RED tests:**

```python
def test_pipeline_executes_stages_in_order():
    """Pipeline should execute stages sequentially."""
    # RED: Not implemented yet

def test_pipeline_passes_output_to_next_stage():
    """Output of stage N should be input to stage N+1."""
    # RED: Not implemented yet

def test_pipeline_error_in_stage_2_stops_execution():
    """Error in stage 2 should stop pipeline, return error."""
    # RED: Not implemented yet

def test_pipeline_realtime_messages_sent():
    """Each stage should emit realtime messages."""
    # RED: Not implemented yet
```

---

## Phase 12 Architecture Diagram

```
[Client Request]
    ↓
[/v1/jobs POST with pipeline definition]
    ↓
[Job created, pipeline assigned]
    ↓
[PipelineExecutor.execute()]
    ├─→ [Stage 1: VideoTracker in sandbox]
    │   └─→ Emit realtime: pipeline_stage_end
    │   └─→ Emit progress: 33% complete
    │
    ├─→ [Stage 2: PoseEstimator in sandbox]
    │   ├─→ Input: output from Stage 1
    │   └─→ Emit realtime: pipeline_stage_end
    │   └─→ Emit progress: 67% complete
    │
    ├─→ [Stage 3: Classifier in sandbox]
    │   ├─→ Input: output from Stage 2
    │   └─→ Emit realtime: pipeline_stage_end
    │   └─→ Emit progress: 100% complete
    │
    └─→ [Return final result]
        ├─→ { ok: true, result: {...}, stages_executed: 3 }
        └─→ or
            { ok: false, error: "...", stage_failed: 2, partial_result: {...} }

[All plugin failures are isolated (Phase 11 guarantee)]
[All lifecycle states updated (Phase 11 guarantee)]
[Realtime WebSocket updates (Phase 10 mechanism)]
```

---

## Phase 12 Success Criteria

Phase 12 is complete when:

✅ **Pipelines run deterministically**
- Same input → same output
- Stages execute in order
- Output flows through stages

✅ **Errors are isolated per stage**
- Stage 1 error doesn't affect Stage 2 config
- Failed plugin marked FAILED in registry
- Partial results returned if Stage N fails

✅ **Realtime updates reflect pipeline state**
- WebSocket messages sent per stage
- Progress updates accurate
- No missing stage events

✅ **All RED tests pass**
- Definition model works
- Executor works
- Messages work
- Partial results work
- Timeouts work

✅ **No Phase 9/10/11 regressions**
- Single-plugin jobs still work
- UI controls still work
- Realtime messaging still works
- Plugin safety still enforced

---

## Out of Scope (Phase 13+)

❌ **Parallel pipeline stages** – Future feature
❌ **Plugin auto-optimization** – Future feature
❌ **GPU task scheduling** – Future feature
❌ **Pipeline marketplace UI** – Future feature
❌ **Plugin composition DAGs** – Future feature
❌ **Conditional branching** – Future feature

Phase 12 is **sequential pipelines only**.

---

## Implementation Timeline

### Week 1: Contracts
- Define pipeline model
- Write RED tests
- Design executor interface
- Design message schema

### Week 2: Foundation
- Implement pipeline model
- Implement executor core
- Implement realtime messages
- Run RED tests (should fail)

### Week 3: Integration
- Wire executor to JobRunner
- Integrate realtime messages with WebSocket
- Implement /v1/pipelines API
- Tests should start passing (GREEN)

### Week 4: Hardening
- Add timeout handling
- Add partial result handling
- Add error recovery
- All tests pass
- No regressions

---

## Key Decisions

### Q: What if Stage 2 expects different input format than Stage 1 provides?

**A:** That's a pipeline design error. Use schema validation.

```python
# In pipeline definition
{
  "stages": [
    { "plugin": "a", "tool": "transform_to_format_x" },
    { "plugin": "b", "tool": "expects_format_x" }  # OK
  ]
}
```

### Q: What if a stage takes too long?

**A:** Timeout per stage (configurable).

```python
pipeline = PipelineDefinition(
    stages=[...],
    timeout_seconds=30.0,  # Per stage
)
```

### Q: What if we want to reuse pipelines?

**A:** Save as templates.

```
POST /v1/pipelines
{
  "name": "soccer-analysis",
  "stages": [...]
}

# Later:
POST /v1/jobs
{
  "pipeline_id": "soccer-analysis",
  "input": {...}
}
```

### Q: Can pipelines call other pipelines?

**A:** No. Out of scope for Phase 12. (Phase 13+)

---

## Rollout Strategy

### 1. Implement silently (Week 1-3)
- No API changes
- New features only
- Tests pass locally

### 2. Beta (Week 4)
- Release with feature flag
- Only internal pipelines
- Gather feedback

### 3. GA (Week 5)
- Feature flag removed
- Default: single-plugin jobs work as before
- Pipelines available for new jobs

---

## Backward Compatibility

**Single-plugin jobs still work:**

```python
# Old API (Phase 11)
POST /v1/jobs
{
  "plugin_id": "videotracker",
  "tool_name": "detect_players",
  "config": {...}
}

# Phase 12: Still works, converted to single-stage pipeline internally
```

---

## Phase 12 Documentation

Once Phase 12 is live:

- [ ] PHASE_12_ARCHITECTURE.md – Full design
- [ ] PHASE_12_RED_TESTS.md – Test contract
- [ ] PHASE_12_PIPELINE_MODEL.md – Data models
- [ ] PHASE_12_EXECUTOR_IMPLEMENTATION.md – Code
- [ ] PHASE_12_EXAMPLES.md – Real pipelines
- [ ] PHASE_12_COMPLETION_CRITERIA.md – Done definition

---

## Next Steps

1. **Complete Phase 11** (this week)
   - Verify all criteria
   - Merge to main
   - Deploy

2. **Kick off Phase 12** (next week)
   - Create `feature/phase-12-orchestration` branch
   - Write RED tests
   - Design executor

3. **Phase 12 design review** (end of week 2)
   - Team review of pipeline model
   - Feedback on executor design
   - Approval to implement

---

**Phase 12 unlocks pipelines.**

**Phase 13 will unlock composition.**

**Phase 14 will unlock marketplace.**

But first: Phase 11 must be complete and solid.

This is the foundation. Build it right.
