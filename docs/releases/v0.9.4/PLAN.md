# v0.9.4 Implementation Plan — Multi-Tool Image Analysis

## Overview

**Goal:** Enable users to submit a single image and execute multiple tools from the same plugin in one job, returning all results in a unified JSON response.

**User Story:** 
> As a user, I would like to analyze an image with multiple tools from the same plugin I have currently selected and return the results in one JSON.

---

## Architecture Summary

```
User → API: POST /v1/image/submit?tool=t1&tool=t2&tool=t3
API → DB: Create job (job_type="image_multi", tool_list=[t1,t2,t3])
Worker → DB: Fetch job
Worker → Plugin: For each tool: run_tool(tool, args)
Worker → DB: Store aggregated results {plugin_id, tools: {t1:..., t2:..., t3:...}}
API → User: Return job_id
User → API: GET /v1/jobs/{job_id} → {status: "completed", results: {...}}
```

---

## Implementation Phases

### Phase 1: Backend — Job Model and Schema Changes

**Files to modify:**
- `server/app/models/job.py`
- `server/app/schemas/job.py`

**Changes:**

#### 1.1 Job Model (`models/job.py`)

Add `tool_list` field and make `tool` nullable for multi-tool jobs:

```python
# Current (line 29)
tool = Column(String, nullable=False)

# New
tool = Column(String, nullable=True)  # Nullable for multi-tool jobs
tool_list = Column(String, nullable=True)  # JSON-encoded list of tools for multi-tool jobs
```

**Note:** Using `String` column with JSON encoding for `tool_list` to avoid adding a new table. Will encode/decode as JSON array.

#### 1.2 Job Schema (`schemas/job.py`)

Add fields to response models:

```python
class JobResultsResponse(BaseModel):
    job_id: UUID
    status: str
    results: dict | None
    tool_list: Optional[List[str]] = None  # NEW: For multi-tool jobs
    job_type: Optional[str] = None  # NEW: "image" | "image_multi"
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
```

**Tests (TDD):**
- Test Job model accepts `tool_list` as JSON string
- Test Job model with `tool=None` and `tool_list` set
- Test schema serialization with `tool_list`

---

### Phase 2: Backend — API Route Changes for Multi-Tool

**Files to modify:**
- `server/app/api_routes/routes/image_submit.py`

**Changes:**

#### 2.1 Accept Multiple Tools

Change query parameter from single string to list:

```python
# Current (line 66)
tool: str = Query(..., description="Tool ID from plugin manifest")

# New
tool: List[str] = Query(..., description="Tool ID(s) from plugin manifest")
```

#### 2.2 Determine Job Type

```python
# Determine job type based on number of tools
if len(tool) > 1:
    job_type = "image_multi"
else:
    job_type = "image"
```

#### 2.3 Validate All Tools Exist

```python
# Validate all tools exist
for t in tool:
    if t not in available_tools:
        raise HTTPException(
            status_code=400,
            detail=f"Tool '{t}' not found in plugin '{plugin_id}'. Available: {available_tools}"
        )
```

#### 2.4 Validate All Tools Support Image Input

```python
# Validate all tools support image input
for t in tool:
    tool_def = plugin.tools.get(t)
    # ... existing validation logic
```

#### 2.5 Create Job with tool_list

```python
import json

job = Job(
    job_id=job_id,
    status=JobStatus.pending,
    plugin_id=plugin_id,
    tool=tool[0] if len(tool) == 1 else None,
    tool_list=json.dumps(tool) if len(tool) > 1 else None,
    input_path=input_path,
    job_type=job_type,
)
```

**Tests (TDD):**
- Test single tool submission creates `job_type="image"`
- Test multi-tool submission creates `job_type="image_multi"`
- Test multi-tool submission stores `tool_list` as JSON
- Test validation rejects invalid tool name
- Test validation rejects tool that doesn't support image input
- Test backward compatibility: single tool still works

---

### Phase 3: Backend — Worker Multi-Tool Execution

**Files to modify:**
- `server/app/workers/worker.py`

**Changes:**

#### 3.1 Detect Multi-Tool Job Type

In `_execute_pipeline()`:

```python
# Determine tools to execute
if job.job_type == "image_multi" and job.tool_list:
    import json
    tools_to_run = json.loads(job.tool_list)
elif job.tool:
    tools_to_run = [job.tool]
else:
    # Error: no tools specified
    job.status = JobStatus.failed
    job.error_message = "No tools specified for job"
    db.commit()
    return False
```

#### 3.2 Execute Tools Sequentially

```python
# Execute each tool and aggregate results
results = {}
for tool_name in tools_to_run:
    # Validate tool supports job_type (existing logic)
    # ...
    
    # Execute tool
    result = plugin_service.run_plugin_tool(job.plugin_id, tool_name, args)
    
    # Handle Pydantic models
    if hasattr(result, "model_dump"):
        result = result.model_dump()
    elif hasattr(result, "dict"):
        result = result.dict()
    
    results[tool_name] = result
```

#### 3.3 Aggregate Results

```python
# Prepare unified output
if job.job_type == "image_multi":
    output_data = {
        "plugin_id": job.plugin_id,
        "tools": results
    }
else:
    output_data = {"results": results[job.tool]}
```

**Tests (TDD):**
- Test worker executes multiple tools sequentially
- Test worker aggregates results into `{"tools": {...}}` format
- Test worker preserves execution order
- Test single-tool job still uses old format
- Test error handling: one tool fails, job status is failed

---

### Phase 4: Frontend — API Client and Types

**Files to modify:**
- `web-ui/src/api/client.ts`

**Changes:**

#### 4.1 Update Job Interface

```typescript
export interface Job {
    job_id: string;
    status: "pending" | "running" | "completed" | "failed";
    plugin_id?: string;
    tool?: string;  // Single tool (backward compatible)
    tool_list?: string[];  // NEW: Multi-tool list
    job_type?: "image" | "image_multi" | "video";  // NEW
    plugin?: string;
    results?: Record<string, unknown>;
    result?: Record<string, unknown>;
    error_message?: string | null;
    error?: string | null;
    created_at: string;
    updated_at?: string;
    completed_at?: string | null;
    progress?: number | null;
}
```

#### 4.2 Update submitImage Method

```typescript
async submitImage(
    file: File,
    pluginId: string,
    tools: string[],  // Changed from single string to array
    onProgress?: (percent: number) => void
): Promise<{ job_id: string }> {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        const url = new URL(`${this.baseUrl}/image/submit`, window.location.origin);
        url.searchParams.append("plugin_id", pluginId);
        
        // Append each tool as separate query parameter
        tools.forEach(t => url.searchParams.append("tool", t));
        
        // ... rest of method
    });
}
```

**Tests (TDD):**
- Test `submitImage` with single tool sends one `tool` param
- Test `submitImage` with multiple tools sends multiple `tool` params
- Test Job interface accepts `tool_list` and `job_type`

---

### Phase 5: Frontend — UI Components for Multi-Tool

**Files to modify:**
- `web-ui/src/App.tsx`
- `web-ui/src/components/ResultsPanel.tsx` (if needed for multi-tool result display)

**Changes:**

#### 5.1 Update handleFileUpload in App.tsx

```typescript
// Current (line 256)
selectedTools[0]

// New
selectedTools  // Pass full array
```

```typescript
const handleFileUpload = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;
      if (!selectedPlugin) return;
      if (selectedTools.length === 0) return;

      setIsUploading(true);
      try {
        // v0.9.4: Pass all selected tools (not just first)
        const response = await apiClient.submitImage(
          file,
          selectedPlugin,
          selectedTools  // CHANGED: was selectedTools[0]
        );
        const job = await apiClient.pollJob(response.job_id);
        setUploadResult(job);
        setSelectedJob(job);
      } catch (err) {
        console.error("Upload failed:", err);
      } finally {
        setIsUploading(false);
      }
    },
    [selectedPlugin, selectedTools]
);
```

#### 5.2 Update ResultsPanel for Multi-Tool Display

If `results.tools` exists, display each tool's result:

```typescript
// In ResultsPanel.tsx
if (job?.results?.tools) {
    // Multi-tool results
    return (
        <div>
            {Object.entries(job.results.tools).map(([toolName, toolResult]) => (
                <div key={toolName}>
                    <h4>{toolName}</h4>
                    <pre>{JSON.stringify(toolResult, null, 2)}</pre>
                </div>
            ))}
        </div>
    );
}
```

**Tests (TDD):**
- Test UI displays multi-tool results correctly
- Test UI still displays single-tool results correctly
- Test handleFileUpload passes all selected tools

---

### Phase 6: Backend Tests (TDD)

**Files to create/modify:**
- `server/tests/api/test_image_submit_multi_tool.py` (NEW)
- `server/tests/workers/test_worker_multi_tool.py` (NEW)

**Test Cases:**

1. **API Tests:**
   - Single tool submission → `job_type="image"`
   - Multi-tool submission → `job_type="image_multi"`
   - Multi-tool validation: invalid tool name → 400
   - Multi-tool validation: tool doesn't support image → 400
   - Backward compatibility: single tool still works

2. **Worker Tests:**
   - Multi-tool job executes all tools
   - Multi-tool job aggregates results
   - Multi-tool job preserves execution order
   - Single-tool job still uses old format
   - Error handling: one tool fails → job fails

3. **Schema Tests:**
   - `JobResultsResponse` serializes `tool_list`
   - `JobResultsResponse` serializes `job_type`

---

### Phase 7: Frontend Tests (TDD)

**Files to create/modify:**
- `web-ui/src/api/client.test.ts` (add multi-tool tests)
- `web-ui/src/App.test.tsx` (add multi-tool submission test)

**Test Cases:**

1. **API Client Tests:**
   - `submitImage` with single tool
   - `submitImage` with multiple tools
   - Query string format: `?tool=a&tool=b&tool=c`

2. **Component Tests:**
   - ResultsPanel displays multi-tool results
   - App passes all selected tools to submitImage

---

### Phase 8: Integration Tests and CI Verification

**Steps:**

1. **Run all backend tests:**
   ```bash
   cd server && uv run pytest tests/ -v
   ```

2. **Run execution governance verification:**
   ```bash
   python scripts/scan_execution_violations.py
   cd server && uv run pytest tests/plugins -v
   cd server && uv run pytest tests/execution -v
   ```

3. **Run all frontend tests:**
   ```bash
   cd web-ui && npm run lint && npm run type-check && npm run test -- --run
   ```

4. **Run pre-commit hooks:**
   ```bash
   uv run pre-commit run --all-files
   ```

5. **Verify CI workflows would pass:**
   - All tests green
   - No lint errors
   - No type errors
   - Coverage maintained

---

## Commit Strategy

Each phase will be a separate commit:

1. **Commit 1:** Phase 1 - Job model and schema changes
2. **Commit 2:** Phase 2 - API route changes for multi-tool
3. **Commit 3:** Phase 3 - Worker multi-tool execution
4. **Commit 4:** Phase 4 - Frontend API client and types
5. **Commit 5:** Phase 5 - Frontend UI components
6. **Commit 6:** Phase 6-8 - Tests and CI verification

---

## Backward Compatibility

- Single-tool jobs continue to work unchanged
- `job.tool` is set for single-tool jobs (backward compatible)
- `job.tool_list` is only set for multi-tool jobs
- API accepts both `tool=a` (single) and `tool=a&tool=b` (multi)

---

## Output Format

### Single-Tool Job (unchanged):
```json
{
  "job_id": "uuid",
  "status": "completed",
  "results": {
    "text": "extracted text..."
  }
}
```

### Multi-Tool Job:
```json
{
  "job_id": "uuid",
  "status": "completed",
  "tool_list": ["player_detection", "ball_detection"],
  "job_type": "image_multi",
  "results": {
    "plugin_id": "yolo-tracker",
    "tools": {
      "player_detection": {"detections": [...]},
      "ball_detection": {"detections": [...]}
    }
  }
}
```

---

## Risk Mitigation

1. **Database Migration:** Using JSON string for `tool_list` avoids new table
2. **Backward Compatibility:** Single-tool path unchanged
3. **Performance:** Sequential execution (parallel can be added later if needed)
4. **Error Handling:** One tool failure fails entire job (simple, predictable)

---

## Definition of Done

- [ ] All phases implemented
- [ ] All tests passing
- [ ] Pre-commit hooks passing
- [ ] CI workflows would pass
- [ ] TDD followed (tests written first)
- [ ] Backward compatibility verified
- [ ] Documentation updated (if needed)