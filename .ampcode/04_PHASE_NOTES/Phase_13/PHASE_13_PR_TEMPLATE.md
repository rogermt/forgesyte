# Phase 13 PR Template — VideoTracker Multi‑Tool Pipelines

Use this template for all Phase 13 pull requests.  
Copy the entire template into your PR description.

---

## PR Title Format

```
feat(phase-13): <specific feature description>
```

Examples:
- `feat(phase-13): Add pipeline execution service`
- `feat(phase-13): Add PipelineToolSelector component`
- `feat(phase-13): Add REST /video/pipeline endpoint`

---

## PR Description

```markdown
# Phase 13 PR — VideoTracker Multi‑Tool Pipelines

## Summary
[Describe the pipeline-related feature implemented in this PR]

## Scope (Required)
This PR includes ONLY:
- [ ] Multi‑tool pipeline support
- [ ] UI pipeline selector
- [ ] REST pipeline endpoint
- [ ] WebSocket pipeline execution
- [ ] Logging for each pipeline step
- [ ] Validation for plugin_id + tools[]

## Out of Scope (Must NOT appear)
- [ ] Cross‑plugin pipelines (FORBIDDEN)
- [ ] Tool parameter UI
- [ ] Model selection
- [ ] Video export
- [ ] Timeline scrubbing
- [ ] Analytics, heatmaps, charts
- [ ] Any UI beyond the canonical VideoTracker spec

## Files Added / Updated

### Server Services
- [ ] `server/app/services/video_pipeline_service.py` (NEW/UPDATED)
- [ ] `server/app/services/vision_analysis_service.py` (UPDATED)

### Server Models
- [ ] `server/app/models/pipeline_models.py` (NEW/UPDATED)

### Server Routes
- [ ] `server/app/routes_video.py` (NEW/UPDATED)

### Server Tests
- [ ] `server/app/tests/test_video_pipeline_rest.py` (NEW)
- [ ] `server/app/tests/test_video_pipeline_ws.py` (NEW)
- [ ] `server/app/tests/test_pipeline_validation.py` (NEW)

### UI Components
- [ ] `web-ui/src/components/VideoTracker/VideoTracker.tsx` (UPDATED)
- [ ] `web-ui/src/components/VideoTracker/PipelineToolSelector.tsx` (NEW)

### UI Hooks
- [ ] `web-ui/src/hooks/useWebSocket.ts` (UPDATED)

### UI API
- [ ] `web-ui/src/api/videoPipeline.ts` (NEW)

### UI Types
- [ ] `web-ui/src/types/pipeline.ts` (NEW)

### Docs
- [ ] `docs/governance/pipeline_rules.md` (NEW/UPDATED)

## Pipeline Validation Checklist

- [ ] Pipeline executes tools in order
- [ ] WebSocket frames include plugin_id + tools[]
- [ ] REST endpoint rejects invalid pipelines
- [ ] Logging shows each pipeline step
- [ ] All tools belong to the same plugin
- [ ] No fallback to default tools
- [ ] No cross‑plugin pipelines allowed

## Testing

- [ ] Unit tests for video_pipeline_service.py
- [ ] REST endpoint tests (POST /video/pipeline)
- [ ] WebSocket pipeline tests (frame processing)
- [ ] Validation tests (invalid plugin_id, invalid tools)
- [ ] Logging tests (step index, tool name)
- [ ] All tests pass: `pytest tests/`
- [ ] UI tests pass: `npm run test -- --run`

## Code Quality

- [ ] Pre-commit hooks pass: `uv run pre-commit run --all-files`
- [ ] Lint clean: `npm run lint` (web-ui)
- [ ] Type-check clean: `npm run type-check` (web-ui)
- [ ] MyPy clean: `uv run mypy app/` (server)
- [ ] No console errors in browser dev tools

## Reviewer Notes

**Critical Checks:**
- Ensure no silent fallbacks exist (no default tool selection)
- Ensure no cross‑plugin pipelines
- Ensure UI sends correct pipeline structure (plugin_id + tools[])
- Verify logging shows each pipeline step
- Verify tools run in order

**Questions for Reviewer:**
- Are pipeline steps validated before execution?
- Does the REST endpoint reject invalid plugin_id?
- Does the REST endpoint reject tools from different plugins?
- Are WebSocket frames logged with step information?

## Related Issues

Closes #XXX (pipeline feature issue)

---

## Sign-Off

- [ ] Author: Code follows Phase 13 spec
- [ ] Author: All tests pass locally
- [ ] Author: PR title matches Phase 13 format
- [ ] Reviewer: All checks above verified
- [ ] Reviewer: No forbidden features found
```

---

## Review Checklist for Maintainers

When reviewing Phase 13 PRs:

1. **Scope Check**
   - [ ] Only Phase 13 features in this PR
   - [ ] No cross‑plugin pipelines
   - [ ] No forbidden features

2. **Structure Check**
   - [ ] Files in correct folders (see PHASE_13_FOLDER_STRUCTURE.md)
   - [ ] Naming conventions followed
   - [ ] No orphaned files

3. **Validation Check**
   - [ ] Pipeline validation implemented
   - [ ] Invalid pipelines rejected with clear error
   - [ ] All tools belong to same plugin

4. **Logging Check**
   - [ ] Pipeline logging present
   - [ ] Step index logged
   - [ ] Tool name logged
   - [ ] No debug logs left in code

5. **Testing Check**
   - [ ] REST tests written
   - [ ] WebSocket tests written
   - [ ] Validation tests written
   - [ ] All tests pass
   - [ ] Coverage >80%

6. **Code Quality Check**
   - [ ] Pre-commit passes
   - [ ] Lint passes
   - [ ] Type-check passes
   - [ ] No console errors

If **any** check fails, request changes before merge.

---

## Merge Criteria

PR can be merged ONLY when:

1. ✅ All above checks pass
2. ✅ No forbidden features detected
3. ✅ Reviewer sign-off obtained
4. ✅ CI/CD pipeline passes
5. ✅ Code follows Phase 13 governance rules
