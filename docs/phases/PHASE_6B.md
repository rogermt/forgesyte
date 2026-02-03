# Phase 6B: Job Pipeline Cleanup & Migration

**Branch**: `refactor/web-ui-job-pipeline-cleanup`  
**GitHub Issue**: [#146](https://github.com/rogermt/forgesyte/issues/146)

## Executive Summary

Remove obsolete tool-runner execution system and consolidate on job pipeline. Six focused deletions/rewires replace direct tool calls with `/v1/analyze` + job polling.

## Architecture: Before & After

### BEFORE (Old System)
```
User Upload
    ↓
[UploadPanel] 
    ↓
runTool(toolId, file)
    ↓
/v1/tools/{id}/run (DIRECT, SYNCHRONOUS)
    ↓
Result (immediate)
    ↓
[ResultsPanel] + detectToolType branching
```

**Problems:**
- Synchronous execution blocks UI
- Tool selection via ToolSelector component (obsolete)
- Type detection logic scattered (`detectToolType`)
- Video tracker calls tools directly

### AFTER (New System)
```
User Upload
    ↓
[UploadPanel]
    ↓
apiClient.analyzeImage(file, pluginId)
    ↓
/v1/analyze (JOB ENDPOINT, RETURNS job_id)
    ↓
apiClient.pollJob(job_id)
    ↓
[JobStatusIndicator] queued → running → done
    ↓
[ResultsPanel] (generic, uses job.result directly)
    ↓
[JobError] (on failure)
```

**Benefits:**
- Non-blocking job queue
- Unified execution path (no special cases)
- UI reflects actual server state (queued/running/done/error)
- Video tracker uses same pipeline

## Files to Delete

| File | Reason |
|------|--------|
| `web-ui/src/components/ToolSelector.tsx` | Tool selection is obsolete; job pipeline is unified |
| `web-ui/src/utils/detectToolType.ts` | Type detection branches removed; job.result is uniform |
| `web-ui/src/api/toolRunner.ts` | Direct tool execution replaced by job pipeline |

## Files to Add

| File | Purpose |
|------|---------|
| `web-ui/src/components/JobStatusIndicator.tsx` | Show queued/running/done/error status |
| `web-ui/src/components/JobError.tsx` | Display error messages with optional retry |
| **Update**: `web-ui/src/components/VideoTracker.tsx` | Use job pipeline instead of direct tool calls |
| **Update**: `web-ui/src/components/UploadPanel.tsx` | Replace `runTool()` with `analyzeImage()` + `pollJob()` |
| **Update**: `web-ui/src/components/ResultsPanel.tsx` | Remove `detectToolType` branching |

## Status

This phase work was defined but not completed. Blocked by:
1. Plugin endpoint stability (issues #100, #124)
2. Job pipeline schema validation
3. Web-UI integration testing

**Current Branch**: `feature/issue-146-job-pipeline-migration` (partial implementation)

See `PHASE_6BC_RECONSTRUCTION.md` for detailed technical specifications.
