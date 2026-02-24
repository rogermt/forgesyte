# v0.9.7 Implementation TODO

## Progress Tracking

- [x] **Phase 1** - API Update for Multi-Tool Video Submit (COMPLETED)
- [x] **Phase 2** - Worker Sequential Execution for Video (COMPLETED)
- [x] **Phase 3** - Unified Progress Tracking (COMPLETED)
- [x] **Phase 4** - Status Endpoint Enhancements (COMPLETED)
- [x] **Phase 5** - Web-UI Tool Selection (Multi-Tool) (COMPLETED)
- [x] **Phase 6** - Web-UI Progress Display (COMPLETED)
- [x] **Phase 7** - Integration Tests ✓ COMPLETED
- [ ] **Phase 8** - Documentation & Smoke Test
- [ ] **Phase 9** - Forgesyte-Plugins: Complete Video Tools

## Implementation Checklist

### Before Starting
- [x] Plan created and approved
- [x] All tests GREEN (1396 Python, 373 Web-UI)
- [ ] Create branch v0.9.7

### Phase 1: API Update ✓ COMPLETED
- [x] Modify `video_submit.py` to accept `List[str]` for tools parameter
- [x] Add backward compatibility for single tool (keep `tool` param)
- [x] Validate all tools support video input
- [x] Save tools to tool_list for multi-tool jobs
- [x] Run pre-commit + tests + governance
- [x] Commit: `feat(api): add multi-tool support to /v1/video/submit`

### Phase 2: Worker Sequential Execution ✓ COMPLETED
- [x] Detect multi-tool video jobs in worker
- [x] Parse tool_list from job
- [x] Loop through tools sequentially
- [x] Store results per tool
- [x] Set progress=100 on completion
- [x] Run pre-commit + tests + governance
- [x] Changes committed to worker.py

### Phase 3: Unified Progress Tracking ✓ COMPLETED
- [x] Modify _update_job_progress for multi-tool
- [x] Calculate tool_weight = 100 / total_tools
- [x] Calculate global_progress with weighting
- [x] Throttle DB updates to 5%
- [x] Ensure final tool reaches 100%
- [x] Run pre-commit + tests + governance ✓
- [x] Changes committed to worker.py

### Phase 4: Status Endpoint Enhancements ✓ COMPLETED
- [x] Add current_tool, tools_total, tools_completed to JobResultsResponse
- [x] Derive fields dynamically in get_job endpoint
- [x] Return progress: None for old jobs
- [x] Run pre-commit + tests + governance
- [x] Commit: `feat(api): extend video job status with multi-tool fields`

### Phase 5: Web-UI Tool Selection ✓ COMPLETED
- [x] Update VideoUpload.tsx for multi-select
- [x] Update client.ts submitVideo() for tools array (already done)
- [x] Run npm lint + type-check + test
- [x] Commit: `feat(ui): add multi-tool selection for video uploads`

### Phase 6: Web-UI Progress Display ✓ COMPLETED
- [x] Add current_tool, tools_total, tools_completed to Job type (already done)
- [x] Update JobStatus.tsx to display tool info
- [x] Run npm lint + type-check + test
- [x] Commit: `feat(ui): display unified progress and current tool for video jobs`

### Phase 7: Integration Tests
- [ ] Create test_multi_tool_video.py
- [ ] Test multi-tool submission
- [ ] Test sequential execution
- [ ] Test progress calculation
- [ ] Test combined results
- [ ] Test backward compatibility
- [ ] Run all tests
- [ ] Commit: `test: add integration tests for multi-tool video execution`

### Phase 8: Documentation & Smoke Test
- [ ] Update smoke_test.py for multi-tool
- [ ] Verify all docs are current
- [ ] Final test run
- [ ] Commit: `docs: add v0.9.7 release docs and update smoke test`

### Phase 9: Forgesyte-Plugins
- [ ] Implement ball_detection_video
- [ ] Implement pitch_detection_video
- [ ] Implement radar_video
- [ ] Implement tracking_video
- [ ] Create _run_video_tool helper
- [ ] Remove device hardcoding
- [ ] Run pre-commit
- [ ] Commit: `feat(plugin): implement remaining video tools with shared helper`

## Final Acceptance
- [ ] Multiple tools run sequentially
- [ ] Combined JSON results keyed by tool ID
- [ ] Unified progress reflects tool index + frame
- [ ] Web-UI displays progress and tool names
- [ ] All pre-commit tests GREEN
- [ ] All Python tests GREEN (1396+)
- [ ] All Web-UI tests GREEN (373+)
- [ ] Governance scan passes
- [ ] Backward compatible

