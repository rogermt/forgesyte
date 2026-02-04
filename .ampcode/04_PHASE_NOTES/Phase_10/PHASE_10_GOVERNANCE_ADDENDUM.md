# Phase 10 Governance Addendum (Minimal)

Lightweight governance rules for Phase 10.

No new global rules. Only Phase 10 constraints.

---

# 1. Scope

This addendum applies ONLY to Phase 10 work in:

```
server/app/realtime/
server/app/models_phase10.py
server/app/plugins/inspector/
server/app/plugins/runtime/ (updates only)
web-ui/src/realtime/
web-ui/src/components/ (3 new components)
web-ui/src/stories/ (1 new story)
```

All Phase 9 code remains unchanged.

---

# 2. Allowed Changes

Phase 10 MAY:

✓ Add new Python modules in `server/app/realtime/`
✓ Add new Python modules in `server/app/plugins/inspector/`
✓ Create `server/app/models_phase10.py`
✓ Update `server/app/plugins/runtime/tool_runner.py` (non-breaking only)
✓ Add new TypeScript modules in `web-ui/src/realtime/`
✓ Add 3 new React components:
  - `ProgressBar.tsx` (with id="progress-bar")
  - `PluginInspector.tsx` (with id="plugin-inspector")
  - `RealtimeOverlay.tsx`
✓ Add 1 new Storybook story: `RealtimeOverlay.stories.tsx`
✓ Add new tests (RED → GREEN)
✓ Modify `.pre-commit-config.yaml` (hook fixes only)
✓ Add new endpoints (`/v1/realtime`, `/v1/jobs/{job_id}/extended`)

---

# 3. Forbidden Changes

Phase 10 MUST NOT:

✗ Modify any Phase 9 API field (job_id, device_requested, device_used, fallback, frames)
✗ Modify any Phase 9 model (`JobResponse`, `FrameData`, etc.)
✗ Remove any Phase 9 endpoint (`GET /v1/jobs/{job_id}`, etc.)
✗ Remove any Phase 9 UI ID (`#device-selector`, `#toggle-*`, `#fps-slider`)
✗ Remove any Phase 9 test
✗ Add schema drift detection
✗ Add new governance rules (beyond this addendum)
✗ Break typed API responses
✗ Break existing Storybook stories
✗ Introduce non-additive changes
✗ Modify `server/app/api/jobs.py` except to add new endpoint

---

# 4. Code Quality Standards

### 4.1 Python (Backend)

- **PEP 8** compliance (enforced by Ruff)
- **Type hints** required for all public functions
- **Docstrings** required for all classes and public functions
- **Error handling**: Catch specific exceptions, use custom types
- **Logging**: Use `logging` module, not `print()`
- **Tests**: All public functions must have tests

Example:
```python
def emit_progress_message(
    job_id: str, progress: int, connection_manager: ConnectionManager
) -> None:
    """Emit a progress message to connected clients.
    
    Args:
        job_id: Job identifier
        progress: Progress percentage (0-100)
        connection_manager: WebSocket connection manager
    
    Raises:
        ValueError: If progress not in range [0, 100]
    """
    if not 0 <= progress <= 100:
        raise ValueError(f"progress must be 0-100, got {progress}")
    
    message = RealtimeMessage(
        type=MessageType.PROGRESS,
        payload={"job_id": job_id, "progress": progress},
        timestamp=datetime.utcnow(),
    )
    asyncio.create_task(connection_manager.broadcast(message.dict()))
```

### 4.2 TypeScript (Frontend)

- **No `any`**: Use proper types or `unknown`
- **Strict mode**: `noImplicitAny`, `strictNullChecks` enabled
- **Type definitions**: All props, state, and API responses typed
- **Comments**: JSDoc for public functions
- **Tests**: All components must have tests

Example:
```typescript
/**
 * Progress bar component for real-time job monitoring.
 * 
 * @param progress - Progress percentage (0-100)
 * @param stage - Human-readable stage description
 */
export function ProgressBar({
  progress,
  stage,
}: {
  progress: number;
  stage?: string;
}): JSX.Element {
  if (progress < 0 || progress > 100) {
    throw new Error(`progress must be 0-100, got ${progress}`);
  }
  return (
    <div id="progress-bar" className="progress-bar">
      <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
      {stage && <p className="progress-bar-label">{stage}</p>}
    </div>
  );
}
```

---

# 5. Testing Requirements

### 5.1 Backend Tests

- **All public functions** must have tests
- **RED → GREEN workflow**: Tests fail before code, pass after
- **Coverage**: Aim for 80%+ on new code
- **Markers**: Use `@pytest.mark.asyncio` for async tests
- **Mocking**: Mock external dependencies (plugins, file I/O)

### 5.2 Frontend Tests

- **All components** must have tests
- **RED → GREEN workflow**: Tests fail before code, pass after
- **Coverage**: Aim for 80%+ on new code
- **Mocking**: Mock WebSocket, RealtimeClient
- **Accessibility**: Test for DOM IDs (#progress-bar, #plugin-inspector)

### 5.3 Integration Tests

- **Realtime flow**: Job starts → progress updates → frames received
- **Error handling**: Connection drops → reconnect works
- **Cleanup**: WebSocket disconnect → no memory leaks

---

# 6. Type Safety

### 6.1 API Responses

All new endpoints MUST return typed responses.

**Example (Backend):**
```python
@router.get("/v1/jobs/{job_id}/extended")
async def get_extended_job(
    job_id: str, db: Session = Depends(get_db)
) -> ExtendedJobResponse:
    """Get extended job with Phase 10 fields."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Return typed response
    return ExtendedJobResponse(
        job_id=job.id,
        device_requested=job.device_requested,
        device_used=job.device_used,
        fallback=job.fallback,
        frames=job.frames,
        progress=job.progress,
        plugin_timings=job.plugin_timings,
        warnings=job.warnings,
    )
```

**Example (Frontend):**
```typescript
interface ExtendedJobResponse {
  job_id: string;
  device_requested: string;
  device_used: string;
  fallback: boolean;
  frames: FrameData[];
  progress?: number;
  plugin_timings?: Record<string, number>;
  warnings?: string[];
}

async function getExtendedJob(jobId: string): Promise<ExtendedJobResponse> {
  const response = await fetch(`/v1/jobs/${jobId}/extended`);
  if (!response.ok) {
    throw new Error(`Failed to fetch job: ${response.statusText}`);
  }
  return response.json() as Promise<ExtendedJobResponse>;
}
```

---

# 7. Backward Compatibility Guarantees

### 7.1 API Compatibility

```
GET /v1/jobs/{job_id}
└─> JobResponse (unchanged, Phase 9)

GET /v1/jobs/{job_id}/extended
└─> ExtendedJobResponse (new, Phase 10, additive)
```

### 7.2 UI Compatibility

Phase 9 UI IDs are preserved:
- `#device-selector`
- `#toggle-*`
- `#fps-slider`

Phase 10 adds:
- `#progress-bar` (new)
- `#plugin-inspector` (new)

No Phase 9 IDs are removed or modified.

### 7.3 Model Compatibility

```python
# Phase 9 (unchanged)
class JobResponse(BaseModel):
    job_id: str
    device_requested: str
    device_used: str
    fallback: bool
    frames: List[FrameData]

# Phase 10 (additive)
class ExtendedJobResponse(JobResponse):
    progress: Optional[int] = None
    plugin_timings: Optional[Dict[str, float]] = None
    warnings: Optional[List[str]] = None
```

---

# 8. Review Checklist

Before merging any Phase 10 PR, verify:

- [ ] All Phase 9 tests still pass
- [ ] All Phase 10 RED → GREEN tests pass
- [ ] No Phase 9 API fields modified
- [ ] No Phase 9 UI IDs removed
- [ ] All new code has type hints
- [ ] All new public functions have docstrings
- [ ] All new components have tests
- [ ] All new endpoints return typed responses
- [ ] `.pre-commit-config.yaml` changes are justified
- [ ] No schema drift detection added
- [ ] No new governance rules added
- [ ] Backward compatibility maintained

---

# 9. Forbidden Patterns

These patterns are NOT allowed in Phase 10:

### 9.1 Python

```python
# ✗ FORBIDDEN: Modifying Phase 9 model
class JobResponse(BaseModel):
    job_id: str
    # ... Phase 9 fields ...
    progress: int  # ✗ Adding to Phase 9 model


# ✓ ALLOWED: Creating new model
class ExtendedJobResponse(JobResponse):
    progress: Optional[int] = None  # ✓ Additive
```

### 9.2 TypeScript

```typescript
// ✗ FORBIDDEN: Using any
function handleMessage(msg: any) {
  // ...
}

// ✓ ALLOWED: Proper typing
interface RealtimeMessage {
  type: string;
  payload: Record<string, unknown>;
  timestamp: string;
}

function handleMessage(msg: RealtimeMessage) {
  // ...
}
```

---

# 10. Enforcement

### 10.1 Continuous Integration

Phase 10 PRs MUST pass:

```bash
# Backend
uv run black app/ tests/ --check
uv run ruff check app/ tests/
uv run mypy app/ --no-site-packages
uv run pytest tests/phase10/ -v

# Frontend
npm run lint
npm run type-check
npm run test -- --run tests/phase10/
```

### 10.2 Manual Review

Phase 10 PRs MUST be reviewed for:

- Phase 9 invariant preservation
- Backward compatibility
- Type safety
- Test coverage
- Code quality

### 10.3 Merge Criteria

Phase 10 PR is mergeable when:

✓ All CI checks pass
✓ All RED → GREEN tests pass
✓ Review checklist complete
✓ No Phase 9 invariants broken
✓ Backward compatibility verified

---

# 11. Examples of Allowed Changes

### Example 1: Adding Real-Time Endpoint

```python
# ✓ ALLOWED: New endpoint, new model
@router.websocket("/v1/realtime")
async def websocket_endpoint(websocket: WebSocket):
    # Phase 10: New functionality
    pass

@router.get("/v1/jobs/{job_id}/extended")
async def get_extended_job(...) -> ExtendedJobResponse:
    # Phase 10: New endpoint
    pass
```

### Example 2: Adding UI Component

```typescript
// ✓ ALLOWED: New component
export function ProgressBar({ progress }: { progress: number }): JSX.Element {
  return <div id="progress-bar">{progress}%</div>;
}

// ✓ ALLOWED: Using new component
export function RealtimeOverlay(): JSX.Element {
  return (
    <div>
      <ProgressBar progress={50} />
    </div>
  );
}
```

---

# 12. Examples of Forbidden Changes

### Example 1: Modifying Phase 9 Model

```python
# ✗ FORBIDDEN: Modifying Phase 9 JobResponse
class JobResponse(BaseModel):
    job_id: str
    device_requested: str
    device_used: str
    fallback: bool
    frames: List[FrameData]
    progress: int  # ✗ Adding to Phase 9 model
```

### Example 2: Removing Phase 9 Test

```python
# ✗ FORBIDDEN: Deleting Phase 9 test
# DO NOT delete or skip tests/api/test_jobs.py
```

### Example 3: Breaking Phase 9 UI

```typescript
// ✗ FORBIDDEN: Removing Phase 9 ID
// DO NOT change #device-selector
export function DeviceSelector(): JSX.Element {
  return <select id="device-selector-v2">  {/* ✗ Wrong ID */}
  </select>;
}
```

---

# 13. Summary

Phase 10 is **strictly additive**:

- New modules, models, endpoints: ✓ Allowed
- Backward compatibility: ✓ Required
- Phase 9 changes: ✗ Forbidden
- Type safety: ✓ Required
- Testing: ✓ Required

This keeps Phase 10 safe, predictable, and driftless.

---

# 14. Questions?

If a change is unclear:

1. Check this addendum
2. Check the PHASE_10_DEVELOPER_CONTRACT.md
3. Assume: If not explicitly allowed, it's forbidden
4. Ask: When in doubt, ask before implementing

