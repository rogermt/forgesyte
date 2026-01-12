# Issue #18: WebUI Test Coverage - Progress Tracking

**Issue**: WebUI Test Coverage Below 80% - App.tsx (33%), JobList (65%)  
**Last Updated**: 2026-01-12 20:00 UTC  
**Current Context Usage**: 15%  
**Overall Progress**: 0/6 work units completed  

---

## Work Unit Status

### Completed
(None yet)

### In Progress
(Ready to start)

### Blocked
(None)

### Todo
- [ ] WU-1: Coverage Setup & Baseline Analysis (45 min)
- [ ] WU-2: JobList Tests Part 1 - Status Rendering (60 min)
- [ ] WU-3: JobList Tests Part 2 - Interactions (60 min)
- [ ] WU-4: App.tsx Tests Part 1 - Header & Navigation (75 min)
- [ ] WU-5: App.tsx Tests Part 2 - Integration (75 min)
- [ ] WU-6: Coverage Verification & Threshold Check (40 min)

---

## Current Work Unit: WU-2
- **Status**: Ready to start
- **Previous (WU-1)**: ✅ COMPLETE - Coverage baseline captured
- **Baseline Overall**: 77.14% (below 80% target)
- **Next Steps**: 
  1. Start with CameraPreview.tsx tests (66.66% → 80%)
  2. Then JobList.tsx tests (65.90% → 80%)
  3. Finally App.tsx tests (47.50% → 80%)

---

## Timeline & Estimates

| Work Unit | Status | Duration | Start | End | Notes |
|-----------|--------|----------|-------|-----|-------|
| WU-1 | TODO | 45 min | - | - | Coverage setup |
| WU-2 | TODO | 60 min | - | - | JobList part 1 |
| WU-3 | TODO | 60 min | - | - | JobList part 2 |
| WU-4 | TODO | 75 min | - | - | App.tsx part 1 |
| WU-5 | TODO | 75 min | - | - | App.tsx part 2 |
| WU-6 | TODO | 40 min | - | - | Verification |
| **TOTAL** | - | **355 min** | - | - | ~6 hours |

---

## Coverage Baseline (Captured in WU-1)

```
Overall: 77.14% (below 80% target)

By Component:
✅ ResultsPanel.tsx    - 100%
✅ PluginSelector.tsx  - 95.45%
✅ client.ts           - 97.87%
✅ useWebSocket.ts     - 87.23%
❌ App.tsx             - 47.50% (gap: +32.5%)
❌ JobList.tsx         - 65.90% (gap: +14.1%)
❌ CameraPreview.tsx   - 66.66% (gap: +13.34%)
```

**Detailed Analysis**: See docs/work-tracking/COVERAGE_BASELINE.md

---

## Branching Strategy

Each work unit uses a feature branch pattern:

```
test-coverage-wu-1 ─┐
test-coverage-wu-2 ─┤
test-coverage-wu-3 ─┤
test-coverage-wu-4 ─┤
test-coverage-wu-5 ─┤
test-coverage-wu-6 ─┴─→ main
```

Commits per WU:
- WU-1: `chore: Setup coverage tools and capture baseline`
- WU-2: `test: Add JobList tests for status rendering and error states`
- WU-3: `test: Complete JobList coverage to 80%+ with interaction tests`
- WU-4: `test: Add App.tsx tests for header and navigation structure`
- WU-5: `test: Complete App.tsx coverage to 80%+ with integration tests`
- WU-6: `test: Verify all components meet 80%+ coverage threshold`

---

## Notes for Next Session

- Plan document created: `docs/work-tracking/ISSUE_18_COVERAGE_PLAN.md`
- Ready to begin WU-1 (coverage setup and baseline)
- All 6 work units defined with clear AC and commit messages
- Total estimated effort: ~6 hours
- No blockers identified

---

## Success Criteria (Final)

- [x] Detailed work plan created
- [ ] WU-1: Baseline captured and gaps documented
- [ ] WU-2: JobList tests for status rendering added
- [ ] WU-3: JobList tests for interactions added
- [ ] WU-4: App.tsx tests for header/nav added
- [ ] WU-5: App.tsx tests for integration added
- [ ] WU-6: All tests pass, coverage 80%+
- [ ] Final verification complete and merged to main

---

**Created**: 2026-01-12 20:00 UTC  
**Plan Ref**: docs/work-tracking/ISSUE_18_COVERAGE_PLAN.md
