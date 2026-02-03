# Architecture Comparison: Before & After Job Pipeline Migration

---

## BEFORE: Old Tool-Runner System

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        AnalyzePage                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐                                            │
│  │  ToolSelector    │ ← Selects plugin to run                    │
│  └────────┬─────────┘                                            │
│           │ setSelectedPluginId                                  │
│           ▼                                                       │
│  ┌────────────────────┐                                          │
│  │  UploadPanel       │ ← Handles file upload                    │
│  │                    │                                          │
│  │  runTool() ────────┼─┐                                        │
│  │            │       │ │                                        │
│  │            └───────┼─┤ PROBLEM: Synchronous call blocks UI   │
│  │                    │ │                                        │
│  │  [Show spinner]    │ │                                        │
│  └────────┬───────────┘ │                                        │
│           │             │                                        │
│           │ (immediate) │                                        │
│           ▼             │                                        │
│  ┌────────────────────┐ │                                        │
│  │  ResultsPanel      │ │                                        │
│  │                    │ │                                        │
│  │ detectToolType()───┼─┤ PROBLEM: Type checking adds branches  │
│  │  if OCR: [Text]    │ │                                        │
│  │  if YOLO: [Boxes]  │ │                                        │
│  │  ...               │ │                                        │
│  └────────────────────┘ │                                        │
│                         │                                        │
└─────────────────────────┼────────────────────────────────────────┘
                          │
                          ▼
                  ┌──────────────────┐
                  │  /v1/tools/{id}  │
                  │      /run        │
                  └──────────────────┘
                   (DIRECT, SYNC)
```

### Data Flow (OLD)

```
User selects plugin
         │
         ▼
User uploads file
         │
         ▼
   runTool(toolId, file)
         │
         ├─► POST /v1/tools/{toolId}/run (SYNC)
         │   blocks UI thread
         │
         ▼ (immediate result or error)
    
setJob({ status: "done", result })
         │
         ▼
detectToolType(plugin_id)
         │
    ┌────┴────┬────────┬────────┐
    │         │        │        │
   OCR      YOLO    Ball   Pitch
    │         │        │        │
    ▼         ▼        ▼        ▼
  Text     Boxes    Position  Field
```

### Problem Summary

❌ **Synchronous Execution**: UI blocks during processing  
❌ **Type Branching**: Complex if/else logic for each plugin type  
❌ **ToolSelector Coupling**: Only used at startup, tightly coupled to execution  
❌ **No Job Queue**: Can't see queued/running/done states  
❌ **Video Tracker Mismatch**: Can't share execution logic with UploadPanel  

---

## AFTER: Unified Job Pipeline

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        AnalyzePage                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────┐                   │
│  │        Plugin Discovery                  │ ← Separate API    │
│  │  (apiClient.listPlugins)                 │                   │
│  │  [Dropdown: Select Plugin]               │                   │
│  └────────────────┬─────────────────────────┘                   │
│                   │ selectedPluginId                            │
│                   ▼                                             │
│  ┌────────────────────────────────────────────┐                 │
│  │  UploadPanel                               │                 │
│  │                                            │                 │
│  │  apiClient.analyzeImage(file, pluginId)   │ ✅ Non-blocking  │
│  │           │                                │                 │
│  │           ▼ { job_id }                     │                 │
│  │                                            │                 │
│  │  apiClient.pollJob(job_id)                 │ ✅ Job status   │
│  │           │                                │                 │
│  │           ▼ Job { status, result, error }  │                 │
│  └────┬──────────────────────────────────────┘                  │
│       │ setJob                                                  │
│       ▼                                                         │
│  ┌────────────────────────────────────────────┐                 │
│  │  JobStatusIndicator                        │ ✅ Unified UI   │
│  │  Shows: queued|running|done|error          │                 │
│  └────────────────────────────────────────────┘                 │
│       │                                                         │
│       ▼                                                         │
│  ┌────────────────────────────────────────────┐                 │
│  │  ResultsPanel                              │ ✅ Generic      │
│  │  <GenericJobResults result={job.result} /> │    rendering    │
│  │                                            │                 │
│  │  (No detectToolType, no branching)         │                 │
│  └────────────────────────────────────────────┘                 │
│       │                                                         │
│       ▼                                                         │
│  ┌────────────────────────────────────────────┐                 │
│  │  JobError                                  │ ✅ Error UI     │
│  │  Shows error message + Retry button        │                 │
│  └────────────────────────────────────────────┘                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
         │                                  │
         │ /v1/analyze                      │ /v1/jobs/{id}
         │                                  │
         ▼                                  ▼
    ┌─────────────────┐         ┌──────────────────────┐
    │  Job Queue      │         │  Job Status Poller   │
    │  (Server-side)  │         │  (Server-side)       │
    └─────────────────┘         └──────────────────────┘
```

### Data Flow (NEW)

```
User selects plugin (via dropdown, separate API)
         │
         ▼
User uploads file
         │
         ▼
apiClient.analyzeImage(file, pluginId)
         │
         ├─► POST /v1/analyze
         │   returns { job_id: "..." }
         │   ✅ Non-blocking
         │
         ▼
apiClient.pollJob(job_id)
         │
         ├─► GET /v1/jobs/{job_id}
         │   (poll until status != "running")
         │   ✅ Shows state transitions
         │
         ▼
setJob({ status: "done", result: {...}, error: null })
         │
    ┌────┴────────────┬──────────────────┐
    │                 │                  │
    ▼                 ▼                  ▼
JobStatusIndicator  ResultsPanel    JobError
 (done)          (generic result)   (null, hidden)


State Machine Example:

setJob → { status: "queued" }
         ▼ [Wait] → 
       { status: "running" }
         ▼ [Wait] →
       { status: "done", result: {...} }
         ▼
    Render all components
    JobStatusIndicator shows "Done"
    ResultsPanel shows job.result
    JobError is null (hidden)
```

### Key Improvements

✅ **Async/Non-blocking**: `analyzeImage()` returns immediately with `job_id`  
✅ **Unified Job Pipeline**: Same code path for all plugins  
✅ **Clear State Transitions**: User sees queued → running → done  
✅ **Generic Rendering**: No branching per plugin type  
✅ **Reusable**: VideoTracker uses same execution logic  
✅ **Error Handling**: Consistent error display and retry  

---

## Component Lifecycle Comparison

### OLD: Synchronous, Type-Specific

```
ToolSelector.tsx
├─► "Select Plugin" dropdown
└─► setSelectedPluginId

UploadPanel.tsx
├─► User selects file
├─► Calls runTool(selectedPluginId, file)
│   └─► POST /v1/tools/{id}/run [BLOCKS]
├─► Receives immediate result
└─► setJob({ status: "done", result })

ResultsPanel.tsx
├─► Calls detectToolType(job.plugin_id)
├─► Maps to renderer:
│   ├─► if "ocr" → OcrResults
│   ├─► if "yolo" → YoloResults
│   └─► if "ball" → BallResults
└─► Renders type-specific component

VideoTracker.tsx (if exists)
├─► Per frame:
│   ├─► Calls runTool(pluginId, frame)
│   │   [BLOCKS]
│   └─► Draws overlays
└─► Can't share logic with UploadPanel
```

### NEW: Asynchronous, Generic

```
AnalyzePage.tsx
├─► Plugin dropdown (via apiClient.listPlugins())
└─► setSelectedPluginId

UploadPanel.tsx
├─► User selects file
├─► Calls apiClient.analyzeImage(file, pluginId)
│   └─► POST /v1/analyze [NON-BLOCKING]
├─► Receives { job_id }
├─► Calls apiClient.pollJob(job_id)
│   └─► GET /v1/jobs/{id} [POLLS until done]
├─► Receives full job { status, result, error }
└─► setJob(job)

JobStatusIndicator.tsx
├─► Shows job.status:
│   ├─► "queued" → "Queued"
│   ├─► "running" → "Running"
│   ├─► "done" → "Done"
│   └─► "error" → "Error"
└─► Returns null if idle (no DOM noise)

ResultsPanel.tsx
├─► Directly renders job.result
├─► No type detection
└─► Generic JSON or card layout

JobError.tsx
├─► Shows job.error message
├─► Optional retry button
└─► Returns null if no error

VideoTracker.tsx (if exists)
├─► Per frame:
│   ├─► Calls apiClient.analyzeImage(frameBlob, pluginId)
│   ├─► Calls apiClient.pollJob(job_id)
│   └─► Draws overlays from job.result
└─► ✅ Same logic as UploadPanel
```

---

## File Structure: Before & After

### BEFORE

```
web-ui/src/
├── components/
│   ├── ToolSelector.tsx          ❌ DELETE
│   ├── UploadPanel.tsx            (runTool import)
│   ├── ResultsPanel.tsx           (detectToolType import)
│   └── VideoTracker.tsx           (runTool import)
├── api/
│   ├── toolRunner.ts             ❌ DELETE
│   └── apiClient.ts              (just HTTP client)
└── utils/
    └── detectToolType.ts          ❌ DELETE
```

### AFTER

```
web-ui/src/
├── components/
│   ├── JobStatusIndicator.tsx    ✅ NEW
│   ├── JobError.tsx              ✅ NEW
│   ├── UploadPanel.tsx            (apiClient import)
│   ├── ResultsPanel.tsx           (generic rendering)
│   └── VideoTracker.tsx           (apiClient import)
├── api/
│   └── apiClient.ts              (has analyzeImage, pollJob)
└── utils/
    (empty or for other things)
```

---

## Server Contract (No Changes Required)

### Input: `/v1/analyze`

```
POST /v1/analyze
Content-Type: multipart/form-data

Body:
  file: <image blob>
  plugin_id: "forgesyte-ocr" | "forgesyte-yolo-tracker" | ...
```

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "queued"
}
```

---

### Polling: `/v1/jobs/{id}`

```
GET /v1/jobs/{job_id}
```

**Response (during processing):**
```json
{
  "id": "uuid-here",
  "status": "running",
  "plugin_id": "forgesyte-ocr",
  "result": null,
  "error": null
}
```

**Response (when done):**
```json
{
  "id": "uuid-here",
  "status": "done",
  "plugin_id": "forgesyte-ocr",
  "result": {
    "text": "extracted text here",
    "confidence": 0.95
  },
  "error": null
}
```

**Response (on error):**
```json
{
  "id": "uuid-here",
  "status": "error",
  "plugin_id": "forgesyte-ocr",
  "result": null,
  "error": "Plugin not found or processing failed"
}
```

---

## Summary Table

| Aspect | BEFORE (Old) | AFTER (New) |
|--------|------|------|
| **Execution Model** | Synchronous | Asynchronous |
| **UI Blocking** | Yes (blocks during processing) | No (returns immediately) |
| **Job Visibility** | None | queued → running → done → error |
| **Result Rendering** | Type-specific branching | Generic, uniform |
| **Type Detection** | `detectToolType()` utility | Not needed |
| **Tool Selection** | `ToolSelector` component | Separate API dropdown |
| **Direct Tool Calls** | `runTool()` | Removed |
| **Video Tracker** | Custom logic, can't share | Uses same pipeline |
| **Error Handling** | Try/catch only | Try/catch + UI component |
| **Code Reuse** | Low | High |
| **Testing** | Mocking `runTool()` | Mocking `apiClient` |

---

## Migration Impact

### What Changes for Users

✅ **Better Feedback**: Users see "Queued" → "Running" → "Done" instead of spinner  
✅ **Faster UI Response**: File upload returns immediately (not blocked)  
✅ **Clearer Errors**: Error messages displayed consistently  
✅ **Retry Option**: Failed jobs can be retried with one click  

### What Stays the Same

✅ Same `/v1/analyze` endpoint (server-side no changes)  
✅ Same job polling mechanism  
✅ Same result format  
✅ Same plugin discovery API  

### Breaking Changes

❌ `runTool()` function removed  
❌ `ToolSelector` component removed  
❌ `detectToolType()` utility removed  
❌ Old tool-runner tests deleted (rewritten for new flow)  

---

## Testing Strategy

### Unit Tests (No API calls)

```
✅ JobStatusIndicator.test.tsx
   - Returns null when idle
   - Shows "Queued", "Running", "Done", "Error" correctly
   - Applies CSS classes

✅ JobError.test.tsx
   - Returns null when no error
   - Shows error message
   - Calls onRetry callback
```

### Component Tests (Mock API)

```
✅ UploadPanel.test.tsx
   - Calls apiClient.analyzeImage(file, pluginId)
   - Calls apiClient.pollJob(job_id)
   - Updates UI with job.status transitions
   - Displays error via JobError

✅ ResultsPanel.test.tsx
   - Renders generic job.result
   - No detectToolType references
   - Handles null result

✅ VideoTracker.test.tsx
   - Processes frames using job pipeline
   - Shows status indicators
   - Handles errors
```

---

## Rollback Strategy

If issues arise:

```bash
# Reset to feature branch start
git reset --hard <original-commit>

# Or reset to main
git checkout main
git reset --hard origin/main
```

No server changes needed (backwards compatible).

---

## Timeline

- **Phase 1 (Deletions)**: 10 min - Remove 3 files
- **Phase 2 (New Components)**: 20 min - Add JobStatusIndicator, JobError
- **Phase 3 (Updates)**: 30 min - Update UploadPanel, ResultsPanel, VideoTracker
- **Phase 4 (Tests)**: 20 min - Write tests for new/updated components
- **Phase 5 (Verification)**: 15 min - Run all tests, lint, type-check
- **Phase 6 (Commit)**: 5 min - Stage and push

**Total**: ~2.5 hours

---

