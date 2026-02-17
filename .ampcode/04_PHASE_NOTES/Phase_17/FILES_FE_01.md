Roger, here are the **four documents**, written cleanly, professionally, and ready to drop straight into your repo or GitHub org.  
They enforce Phase 17 governance, prevent regressions, and give your dev a crystal‑clear contract to follow.

I’ve written them in a tone that’s firm, explicit, and contributor‑friendly — exactly what a high‑stakes migration like this needs.

---

# 🔥 1. **GitHub PR Template — Phase 17 Enforcement**

Save as:  
`.github/pull_request_template.md`

```md
# Phase 17 Pull Request Checklist

This PR will not be reviewed unless **ALL** items below are checked.

## ✅ Architecture Compliance
- [ ] No Phase 10 or Phase 14 components added or modified
- [ ] No plugin/tool/manifest logic anywhere
- [ ] No pipelineId usage in any file
- [ ] No references to runTool, useVideoProcessor, useManifest, useVideoExport
- [ ] No JSON-frame WebSocket logic (must be binary JPEG)
- [ ] No new global state outside RealtimeContext or MP4ProcessingContext

## ✅ File Structure Compliance
- [ ] All new API types added to `src/api/types.ts`
- [ ] All global styles live in `src/styles/globals.css`
- [ ] No new files added under `src/components/plugins/`, `tools/`, or `upload/`

## ✅ Streaming Path Compliance
- [ ] WebSocket endpoint is `/ws/video/stream`
- [ ] Outgoing frames are binary JPEG
- [ ] Incoming frames parsed as binary + metadata
- [ ] RealtimeContext updated correctly

## ✅ MP4 Upload Compliance
- [ ] Uses `useMP4Upload` (NOT useVideoProcessor)
- [ ] Upload → job → poll → complete flow implemented
- [ ] MP4ProcessingContext updated correctly
- [ ] StreamDebugPanel shows MP4 metrics

## ✅ Tests
- [ ] No Phase 10 tests remain
- [ ] No skipped tests
- [ ] All Phase 17 tests pass locally

## Summary
Explain what this PR changes and why it is Phase 17 compliant:

```
(Write summary here)
```
```

This template **forces** the dev to think in Phase 17 terms.

---

# 🔥 2. **CI Rule — Block Phase 10 Imports**

Save as:  
`.github/workflows/block-legacy.yml`

```yaml
name: Block Legacy Phase 10 Code

on:
  pull_request:
    branches: [ main, master ]

jobs:
  block_legacy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Search for forbidden legacy imports
        run: |
          forbidden=(
            "useVideoProcessor"
            "useManifest"
            "useVideoExport"
            "runTool"
            "detectToolType"
            "plugin"
            "tool"
            "pipelineId"
            "ResultsPanel"
            "PluginSelector"
            "ToolSelector"
            "RealtimeOverlay"
          )

          for term in "${forbidden[@]}"; do
            if grep -R "$term" src/; then
              echo "❌ Forbidden legacy reference found: $term"
              exit 1
            fi
          done

      - name: Passed
        run: echo "✅ No legacy Phase 10/14 code detected"
```

This CI rule **prevents regressions** and stops the dev from reintroducing legacy code.

---

# 🔥 3. **Phase 17 Definition of Done (DoD)**

Save as:  
`PHASE_17_DEFINITION_OF_DONE.md`

```md
# Phase 17 — Definition of Done

A feature, fix, or refactor is considered **DONE** only when ALL of the following conditions are met.

---

## 1. Architecture
- The change aligns with the Phase 17 Final Architecture.
- No Phase 10 or Phase 14 code paths remain.
- No plugin/tool/manifest logic exists.
- No pipelineId is used anywhere.
- All streaming logic uses binary JPEG frames.
- All MP4 upload logic uses the job pipeline.

---

## 2. File Structure
- All API types live in `src/api/types.ts`.
- All global styles live in `src/styles/globals.css`.
- No new files are added under legacy directories:
  - `src/components/plugins/`
  - `src/components/tools/`
  - `src/components/upload/`

---

## 3. Streaming Path
- WebSocket endpoint is `/ws/video/stream`.
- CameraPreview sends binary JPEG frames.
- useWebSocket parses binary frames + metadata.
- RealtimeContext receives structured detection data.
- RealtimeStreamingOverlay renders correctly.

---

## 4. MP4 Upload Path
- MP4 upload uses `useMP4Upload`.
- VideoTracker uses `useMP4Upload`.
- MP4ProcessingContext exposes:
  - status
  - jobId
  - progress
  - framesProcessed
  - error
- StreamDebugPanel displays MP4 metrics.

---

## 5. Tests
- All Phase 10 tests removed.
- No skipped tests.
- All Phase 17 tests pass.
- No tests reference plugin/tool/manifest/pipelineId.

---

## 6. Manual Verification
- Stream mode works end-to-end.
- Upload mode works end-to-end.
- Jobs mode loads job history.
- Debug panel shows streaming + MP4 metrics.

---

## 7. Code Quality
- No unused imports.
- No dead files.
- No console errors.
- No TODOs referencing Phase 10 or Phase 14.

---

If ANY of these conditions are not met, the work is **NOT DONE**.
```

This DoD gives you a **single source of truth** for completion.

---

# 🔥 4. **Phase 17 Architecture Contract (Contributor Agreement)**

Save as:  
`PHASE_17_ARCHITECTURE_CONTRACT.md`

```md
# Phase 17 Architecture Contract

All contributors must follow this contract when modifying the web-ui codebase.

---

## 1. No Legacy Architecture
You may NOT introduce or modify:
- plugin logic
- tool logic
- manifest loading
- pipeline selection
- pipelineId usage
- runTool or useVideoProcessor
- any Phase 10 or Phase 14 component

These architectures are permanently removed.

---

## 2. Streaming Rules
- WebSocket endpoint MUST be `/ws/video/stream`.
- Outgoing frames MUST be binary JPEG.
- Incoming frames MUST be binary JPEG + JSON metadata.
- No base64 images.
- No JSON-frame streaming.
- No plugin_id or tool_id fields.

---

## 3. MP4 Upload Rules
- MP4 upload MUST use `useMP4Upload`.
- VideoTracker MUST NOT use useVideoProcessor.
- MP4 jobs MUST be polled via `/api/jobs/{id}`.
- MP4ProcessingContext MUST be updated.

---

## 4. File Structure Rules
- All API types MUST be in `src/api/types.ts`.
- All global styles MUST be in `src/styles/globals.css`.
- No new files may be added under:
  - `src/components/plugins/`
  - `src/components/tools/`
  - `src/components/upload/`

---

## 5. Test Rules
- No Phase 10 tests may remain.
- No skipped tests allowed.
- All new tests MUST target Phase 17 behavior.

---

## 6. Forbidden Terms
The following MUST NOT appear anywhere in the codebase:

```
plugin
tool
manifest
pipelineId
runTool
useVideoProcessor
useManifest
useVideoExport
detectToolType
ResultsPanel
PluginSelector
ToolSelector
RealtimeOverlay
```

CI will block PRs containing these terms.

---

## 7. Enforcement
- CI will reject PRs violating this contract.
- Reviewers will reject PRs violating this contract.
- Contributors must fix violations before merging.

---

By contributing to this repository, you agree to follow the Phase 17 Architecture Contract.
```

This contract **locks the architecture** and prevents future drift.

---

# Roger — you now have:

### ✔ A PR template enforcing Phase 17  
### ✔ A CI rule blocking legacy imports  
### ✔ A Definition of Done  
### ✔ An Architecture Contract  

