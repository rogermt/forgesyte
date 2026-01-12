# Issue #18: Test Coverage Below 80% - Executive Summary

**Status**: Work Plan Created  
**Issue**: App.tsx (33%), JobList (65%)  
**Goal**: Reach 80%+ coverage for all WebUI components  
**Total Effort**: ~6 hours across 6 work units  

---

## Quick Start

### Before Beginning Work

Run this to capture baseline coverage:

```bash
cd /home/rogermt/forgesyte/web-ui
npm install @vitest/coverage-v8
npm run test:coverage 2>&1 | tee coverage-baseline.txt
```

Save the baseline output for comparison after all work units complete.

---

## Work Units at a Glance

| WU | Task | Duration | Gap | Status |
|----|------|----------|-----|--------|
| 1 | Setup coverage tools & baseline | 45 min | N/A | TODO |
| 2 | JobList tests (status/errors) | 60 min | 65% → 75% | TODO |
| 3 | JobList tests (interactions) | 60 min | 75% → 80% | TODO |
| 4 | App.tsx tests (header/nav) | 75 min | 33% → 50% | TODO |
| 5 | App.tsx tests (integration) | 75 min | 50% → 80% | TODO |
| 6 | Verify 80%+ threshold | 40 min | N/A | TODO |

---

## Key Commit Strategy

Each WU gets its own feature branch and commit:

```
git checkout -b test-coverage-wu-1
# ... add tests ...
git commit -m "chore: Setup coverage tools and capture baseline"
git push origin test-coverage-wu-1
git checkout main && git merge test-coverage-wu-1 && git push origin main

# Repeat for WU-2 through WU-6
```

---

## Testing Focus Areas

### JobList (WU-2, WU-3)
- Job status badges (pending, processing, completed, failed)
- Error message display
- Empty state handling
- Job interactions (click, hover)
- Data refresh/pagination if applicable

### App.tsx (WU-4, WU-5)
- Header rendering and branding
- Navigation mode switching (stream vs upload)
- Brand color verification
- WebSocket integration
- Error boundaries
- Conditional rendering logic

---

## Important Notes

1. **Use `vi.mock()` for external dependencies**: WebSocket hook, API calls, browser APIs
2. **Test behavior, not styling**: Focus on functional coverage, not CSS tests
3. **One assertion per test** where possible
4. **Mock all external calls**: No real API calls or browser API access in tests
5. **Run tests frequently**: `npm run test` after each test addition

---

## Progress Tracking

- **Plan Document**: `docs/work-tracking/ISSUE_18_COVERAGE_PLAN.md`
- **Progress File**: `docs/work-tracking/ISSUE_18_PROGRESS.md`
- **Baseline File**: `web-ui/coverage-baseline.txt` (created in WU-1)

Update Progress.md after each work unit with:
- Start/end times
- Actual vs estimated effort
- Coverage % improvements
- Any blockers encountered

---

## Definition of Done

For each work unit:
- [ ] All new tests pass: `npm run test`
- [ ] Coverage increased toward target
- [ ] No console errors/warnings
- [ ] Feature branch pushed
- [ ] Merged to main
- [ ] Progress.md updated

For the entire issue:
- [ ] App.tsx: 80%+ coverage
- [ ] JobList.tsx: 80%+ coverage
- [ ] All tests pass
- [ ] Coverage report generated
- [ ] Merged to main

---

## First Steps (WU-1)

```bash
cd /home/rogermt/forgesyte

# Create feature branch
git checkout -b test-coverage-wu-1

# Install coverage dependency if missing
cd web-ui
npm install @vitest/coverage-v8

# Run baseline
npm run test:coverage 2>&1 | tee coverage-baseline.txt

# Analyze output and document gaps
# Update Progress.md with baseline numbers

# Commit
git add .
git commit -m "chore: Setup coverage tools and capture baseline"
git push origin test-coverage-wu-1

# Merge to main
git checkout main
git merge test-coverage-wu-1
git push origin main
```

---

## References

- **Coverage Plan**: docs/work-tracking/ISSUE_18_COVERAGE_PLAN.md
- **Progress Tracker**: docs/work-tracking/ISSUE_18_PROGRESS.md
- **Related Issue**: #18 (this issue)
- **Related Components**: 
  - `web-ui/src/components/App.tsx` (33% coverage)
  - `web-ui/src/components/JobList.tsx` (65% coverage)
  - `web-ui/src/components/CameraPreview.tsx` (45% coverage - analyzed separately)

---

**Created**: 2026-01-12 20:00 UTC  
**Ready to Begin**: Yes
