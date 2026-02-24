# 📄 **docs/releases/v0.9.7/OVERVIEW.md**

```markdown
# v0.9.7 — Multiple Tools on Videos (Sequential Execution)

## Summary
v0.9.7 extends the video analysis pipeline to support running **multiple tools from the same plugin** on a single uploaded video. Tools execute **sequentially**, results are **combined**, and progress is **unified** across all tools using equal weighting. This brings video processing to parity with the multi‑tool image workflow introduced in v0.9.5.

## Key Features
- `/v1/video/submit` now accepts `"tools": []` (with `"tool"` still supported)
- Worker executes video tools sequentially on the same video
- Unified progress tracking across tools
- Combined JSON results keyed by tool ID
- Web‑UI supports multi‑tool selection and displays current tool + progress

## Compatibility
- Fully backward compatible with single‑tool video jobs
- Old jobs without progress return `"progress": null`
- No plugin manifest changes required

## Motivation
This release enables richer football analytics workflows (player detection, ball detection, pitch detection, radar, etc.) in a single job and prepares the system for future multi‑stage pipelines in v1.0.0.


## Key Features
- Support for `"tools": []` in `/v1/video/submit`
- Sequential execution of multiple video tools from the same plugin
- Unified progress tracking across tools
- Combined JSON results keyed by tool ID
- Web‑UI updates to display current tool and progress

## Compatibility
- Backward compatible with single‑tool video jobs
- Old jobs without progress tracking return `"progress": null`
- No breaking changes to plugin manifests

## Motivation
This release brings video analysis to parity with image analysis and lays the foundation for future multi‑stage pipelines in v1.0.0.
```

---

Here you go, Roger — **clean, sharp, production‑ready** deliverables for v0.9.7:

- **PR description**
- **Commit message set**
- **Smoke test update**

All aligned with your v0.9.7 spec:  
**multiple tools on videos, sequential execution, unified progress, combined results.**

No fluff, no drift — just the exact content your dev team expects.

---

# ⭐ **PR DESCRIPTION — v0.9.7 Multi‑Tool Video Execution**

```markdown
# v0.9.7 — Multi‑Tool Video Execution (Sequential)

## Summary
This PR extends the existing video analysis pipeline to support running **multiple tools from the same plugin** on a single uploaded video. Tools are executed **sequentially**, results are **combined into a single JSON response**, and progress is **unified across all tools** using equal weighting.

This brings video processing to parity with the multi‑tool image workflow introduced in v0.9.5.

## Key Features
- `/v1/video/submit` now accepts `"tools": []` in addition to `"tool"`
- Worker executes tools sequentially on the same video
- Unified progress tracking across tools (equal weighting)
- Status endpoint returns:
  - `current_tool`
  - `tools_total`
  - `tools_completed`
  - `progress`
- Combined JSON results keyed by tool ID
- Web‑UI updated to support multi‑tool selection and display progress

## Technical Changes
### API
- Added support for `"tools": []` in video submission
- Backward compatible with `"tool": "..."`

### Worker
- Sequential execution loop
- Per‑tool progress mapped into global progress
- Combined results stored in job record
- Ensures progress reaches 100% on completion

### Plugin
- Video tools already support `progress_callback` from v0.9.6
- No manifest changes required

### Web‑UI
- Multi‑tool selector for video tools
- Progress bar shows unified progress
- Displays current tool and completed tool count

## Backward Compatibility
- Single‑tool video jobs continue to work unchanged
- Old jobs without progress return `"progress": null`

## Testing
- Added multi‑tool video tests
- Updated smoke test to validate multi‑tool behavior
- Updated UI tests for multi‑tool selection and progress display

## Motivation
This feature enables richer football analytics workflows (player detection, ball detection, pitch detection, radar, etc.) in a single job and prepares the system for future multi‑stage pipelines in v1.0.0.
```

---

# ⭐ **COMMIT MESSAGE SET — v0.9.7**

These are the exact commits your dev should make, one per phase.

---

### **Commit 1 — API**
```
feat(api): add multi-tool support to /v1/video/submit

- Accepts "tools": [] for video jobs
- Normalizes "tool" to ["tool"] for backward compatibility
- Validates tools belong to the selected plugin
```

---

### **Commit 2 — Worker Execution**
```
feat(worker): implement sequential multi-tool video execution

- Executes video tools sequentially on the same video
- Stores results per tool in combined result object
- Tracks current_tool, tools_total, tools_completed
```

---

### **Commit 3 — Unified Progress**
```
feat(worker): add unified progress tracking across video tools

- Equal weighting per tool
- Maps per-tool frame progress into global progress
- Updates DB every 5% to reduce write load
```

---

### **Commit 4 — Status Endpoint**
```
feat(api): extend video job status with multi-tool fields

- Adds current_tool, tools_total, tools_completed
- Returns progress from DB
- Returns progress: null for old jobs
```

---

### **Commit 5 — Web‑UI**
```
feat(ui): add multi-tool video selection and progress display

- Allows selecting multiple video tools
- Shows progress bar, current tool, and completed tool count
- Polls status endpoint every 2 seconds
```

---

### **Commit 6 — Tests**
```
test: add tests for multi-tool video execution and progress

- Multi-tool submission tests
- Sequential execution tests
- Progress calculation tests
- UI tests for multi-tool selection and progress bar
- Updated smoke test
```

---

