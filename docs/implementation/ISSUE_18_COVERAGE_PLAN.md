# Issue #18: WebUI Test Coverage Below 80% - Work Unit Plan

**Created**: 2026-01-12  
**Issue**: App.tsx (33%), JobList (65%)  
**Goal**: Reach 80%+ coverage for all WebUI components  

---

## Initial Baseline (Before Work Begins)

Run this command to capture baseline coverage:

```bash
cd /home/rogermt/forgesyte/web-ui
npm install @vitest/coverage-v8  # Install if missing
npm run test:coverage 2>&1 | tee coverage-baseline.txt
```

**Expected Components Below 80%**:
- `App.tsx` - ~33% (needs ~47% more)
- `JobList.tsx` - ~65% (needs ~15% more)
- Other components to check as we go

---

## Work Unit Strategy

### Phases
1. **Setup** (WU-1): Install coverage tools, run baseline, analyze gaps
2. **Fix JobList** (WU-2, WU-3): Easier target (65% → 80%, needs ~15%)
3. **Fix App.tsx** (WU-4, WU-5): Harder target (33% → 80%, needs ~47%)
4. **Verify** (WU-6): Run full coverage check, ensure 80%+ threshold

---

## Work Units

### WU-1: Coverage Setup & Baseline Analysis
**Estimated**: 30-45 minutes  
**Acceptance Criteria**:
- [ ] `@vitest/coverage-v8` installed in web-ui
- [ ] Baseline coverage report generated (saved as `coverage-baseline.txt`)
- [ ] Coverage analysis document created with exact coverage % per file
- [ ] Gap analysis complete (what tests needed for each file)

**Commit**: `chore: Setup coverage tools and capture baseline`

**Steps**:
```bash
cd /home/rogermt/forgesyte/web-ui

# 1. Install coverage dependency
npm install @vitest/coverage-v8

# 2. Run baseline
npm run test:coverage 2>&1 | tee coverage-baseline.txt

# 3. Analyze output and document gaps
# Create docs/COVERAGE_GAPS.md with:
# - Current % for each component
# - Lines/functions missing tests
# - Specific test cases needed
```

---

### WU-2: JobList Component - Tests Part 1
**Estimated**: 45-60 minutes  
**Current**: 65% → Target: 75% (intermediate)  
**Acceptance Criteria**:
- [ ] Add tests for job rendering with different statuses
- [ ] Add tests for error display
- [ ] Add tests for empty state
- [ ] Coverage increases to 72-75%

**Commit**: `test: Add JobList tests for status rendering and error states`

**Focus Areas** (from coverage gaps):
- Job status indicators (pending, processing, completed, failed)
- Error message display
- Empty job list handling
- Loading state

**Test Template**:
```typescript
describe("JobList", () => {
  describe("status rendering", () => {
    it("should render pending status badge");
    it("should render processing status badge");
    it("should render completed status badge");
    it("should render failed status badge");
  });
  
  describe("error handling", () => {
    it("should display error message when provided");
    it("should apply error styling");
  });
  
  describe("empty state", () => {
    it("should show empty message when no jobs");
  });
});
```

---

### WU-3: JobList Component - Tests Part 2
**Estimated**: 45-60 minutes  
**Current**: 75% → Target: 80%+  
**Acceptance Criteria**:
- [ ] Add tests for job interactions (click, hover)
- [ ] Add tests for filtering/sorting if applicable
- [ ] Add tests for pagination if applicable
- [ ] Coverage increases to 80%+

**Commit**: `test: Complete JobList coverage to 80%+ with interaction tests`

**Focus Areas**:
- Job selection/click handling
- Data refresh/polling if applicable
- Pagination controls if applicable
- Sort/filter controls if applicable

---

### WU-4: App.tsx Component - Tests Part 1
**Estimated**: 60-90 minutes  
**Current**: 33% → Target: 50% (intermediate)  
**Acceptance Criteria**:
- [ ] Add tests for header rendering (branding, layout)
- [ ] Add tests for navigation/mode switching (stream vs upload)
- [ ] Add tests for theme/styling
- [ ] Coverage increases to 48-52%

**Commit**: `test: Add App.tsx tests for header and navigation structure`

**Focus Areas** (from analysis):
- Header component rendering
- Navigation buttons/tabs
- Mode switching logic (stream mode vs upload mode)
- Brand styling verification

**Test Template**:
```typescript
describe("App", () => {
  describe("header", () => {
    it("should render ForgeSyte branding");
    it("should render navigation tabs");
    it("should use ForgeSyte brand colors");
  });
  
  describe("mode switching", () => {
    it("should switch to stream mode");
    it("should switch to upload mode");
    it("should update layout when switching modes");
  });
});
```

---

### WU-5: App.tsx Component - Tests Part 2
**Estimated**: 60-90 minutes  
**Current**: 50% → Target: 80%+  
**Acceptance Criteria**:
- [ ] Add tests for WebSocket connection state integration
- [ ] Add tests for error boundaries
- [ ] Add tests for layout conditional rendering
- [ ] Add tests for plugin selection integration
- [ ] Coverage increases to 80%+

**Commit**: `test: Complete App.tsx coverage to 80%+ with integration tests`

**Focus Areas**:
- WebSocket state changes affecting UI
- Error handling and error messages
- Conditional rendering of components (stream view vs upload view)
- Plugin state integration
- Results panel display logic

---

### WU-6: Coverage Verification & Threshold Check
**Estimated**: 30-45 minutes  
**Acceptance Criteria**:
- [ ] All tests pass: `npm run test`
- [ ] Coverage report generated: `npm run test:coverage`
- [ ] All components 80%+: `npm run test:coverage | grep -E "(App|JobList|CameraPreview)"`
- [ ] No regressions in other components
- [ ] Final coverage report saved
- [ ] PR ready for review

**Commit**: `test: Verify all components meet 80%+ coverage threshold`

**Steps**:
```bash
cd /home/rogermt/forgesyte/web-ui

# 1. Run full test suite
npm run test

# 2. Generate coverage report
npm run test:coverage

# 3. Compare with baseline
# Review coverage-baseline.txt vs new report

# 4. Verify threshold met
npm run test:coverage 2>&1 | grep "% of statements"
```

---

## Testing Approach

### Mock Requirements
For comprehensive testing, ensure these are mocked:

**WebSocket Hook** (`useWebSocket`):
```typescript
vi.mock("../hooks/useWebSocket", () => ({
  useWebSocket: vi.fn(() => ({
    connect: vi.fn(),
    disconnect: vi.fn(),
    send: vi.fn(),
    isConnected: true,
    // ... other required fields
  })),
}));
```

**API Calls** (if applicable):
```typescript
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ /* mock data */ }),
  })
);
```

**Browser APIs** (Camera, Canvas):
```typescript
navigator.mediaDevices = {
  getUserMedia: vi.fn(),
  enumerateDevices: vi.fn(),
};
```

---

## Key Testing Principles

1. **One assertion per test** where possible
2. **Mock external dependencies** (API calls, browser APIs)
3. **Test behavior, not implementation** (don't rely on internal state)
4. **Cover edge cases** (errors, empty data, disabled states)
5. **Use descriptive test names** (should clearly state what is tested)

---

## Git Workflow

For each work unit:

```bash
# Create feature branch
git checkout -b test-coverage-wu-X

# Make commits as you add tests
git add .
git commit -m "test: [WU-X description]"

# Push when WU is complete
git push origin test-coverage-wu-X

# After WU complete, merge locally
git checkout main
git pull origin main
git merge test-coverage-wu-X
git push origin main
```

---

## Coverage Thresholds by Component

| Component | Current | Target | Gap |
|-----------|---------|--------|-----|
| App.tsx | 33% | 80% | +47% |
| JobList.tsx | 65% | 80% | +15% |
| CameraPreview.tsx | ~45% | 80% | +35% (analyzed separately) |
| PluginSelector.tsx | TBD | 80% | TBD |
| Others | TBD | 80% | TBD |

---

## Success Metrics

- [ ] App.tsx: 80%+ coverage
- [ ] JobList.tsx: 80%+ coverage
- [ ] All test files pass with `npm run test`
- [ ] No console errors or warnings
- [ ] Code review approved
- [ ] Merged to main branch

---

## Related Issues

- #18 - WebUI test coverage (THIS ISSUE)
- #17 - WebSocket infinite reconnection (FIXED)
- #19 - Frame validation error (open, WebSocket-related)

---

## Notes

- Coverage dependency may need to be added to package.json devDependencies
- Focus on **behavior testing**, not styling tests (those are already in place)
- Use vitest `vi.mock()` for mocking hooks and external dependencies
- Consider integration tests for components that work together (App + WebSocket + JobList)

---

**Plan Created**: 2026-01-12 19:55 UTC  
**Next Step**: Run WU-1 to establish baseline and detailed gaps
