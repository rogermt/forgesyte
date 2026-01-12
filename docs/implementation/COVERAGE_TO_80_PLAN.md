# WebUI Test Coverage to 80% - Comprehensive Plan

**Status**: Active  
**Current Overall**: 77.14%  
**Target**: 80%+ for all components  
**Created**: 2026-01-12 20:00 UTC  

---

## Executive Summary

WebUI coverage is at **77.14%** (below 80% target). Three components need work:

| Component | Current | Target | Gap | Priority |
|-----------|---------|--------|-----|----------|
| App.tsx | 47.50% | 80% | +32.5% | **CRITICAL** |
| JobList.tsx | 65.90% | 80% | +14.1% | **HIGH** |
| CameraPreview.tsx | 66.66% | 80% | +13.34% | **HIGH** |

**Already Passing**: ResultsPanel.tsx (100%), PluginSelector.tsx (95.45%), useWebSocket.ts (87.23%), client.ts (97.87%)

---

## Work Unit Breakdown

### WU-1: Coverage Setup ✅ DONE
- Installed @vitest/coverage-v8
- Ran baseline: 77.14% overall
- Documented gaps in COVERAGE_BASELINE.md
- **Commit**: `chore: Setup coverage tools and capture baseline`

---

### WU-2: CameraPreview.tsx Tests (2-3 hours)

**Current**: 66.66% → **Target**: 80% (+13.34%)

**Uncovered Lines**: 51-75, 91-108, 184-196

**Test Cases Needed**:

```typescript
describe("CameraPreview - Device Management", () => {
  it("should enumerate video devices on mount");
  it("should auto-select first device if available");
  it("should update device list when devices change");
  it("should handle enumeration errors gracefully");
});

describe("CameraPreview - Camera Lifecycle", () => {
  it("should start camera stream when enabled=true");
  it("should request correct media constraints");
  it("should set video element srcObject to stream");
  it("should set isStreaming=true on success");
  it("should stop camera stream when enabled=false");
  it("should stop all tracks on stop");
  it("should handle getUserMedia permission denied");
  it("should clear error on successful start");
});

describe("CameraPreview - Frame Capture", () => {
  it("should capture frame at specified interval");
  it("should call onFrame with base64 data");
  it("should not capture when disabled");
  it("should not capture when not streaming");
  it("should handle missing canvas context");
  it("should convert frame to JPEG with correct quality");
});

describe("CameraPreview - Device Selection UI", () => {
  it("should show device selector when multiple devices");
  it("should hide selector when only one device");
  it("should call setSelectedDevice on change");
});
```

**Mocks Required**:
```typescript
navigator.mediaDevices.getUserMedia = vi.fn();
navigator.mediaDevices.enumerateDevices = vi.fn();
HTMLVideoElement.prototype.play = vi.fn(async () => {});
canvas.getContext("2d") mock
```

**Commit**: `test: Add CameraPreview tests - device mgmt, lifecycle, capture (66.66% → 80%)`

---

### WU-3: JobList.tsx Tests (2-3 hours)

**Current**: 65.90% → **Target**: 80% (+14.1%)

**Uncovered Lines**: 36-42, 60-62, 109-130

**Test Cases Needed**:

```typescript
describe("JobList - Job Rendering", () => {
  it("should render list of jobs");
  it("should display job ID");
  it("should display job status");
  it("should display job result summary");
  it("should display submission timestamp");
});

describe("JobList - Status Indicators", () => {
  it("should show pending status badge");
  it("should show processing status badge");
  it("should show completed status badge");
  it("should show failed status badge");
  it("should apply correct styling for each status");
});

describe("JobList - Error States", () => {
  it("should display error message when provided");
  it("should show error styling");
  it("should display error details in expanded view");
});

describe("JobList - Empty State", () => {
  it("should show empty message when no jobs");
  it("should show placeholder or hint text");
});

describe("JobList - Job Interactions", () => {
  it("should expand job on click");
  it("should collapse job on second click");
  it("should show full results when expanded");
  it("should handle job selection");
});

describe("JobList - Data Display", () => {
  it("should format timestamps correctly");
  it("should truncate long result summaries");
  it("should show processing progress if available");
});
```

**Mocks Required**:
```typescript
Mock job data with various statuses
Mock API response data
Mock timestamp formatting
```

**Commit**: `test: Add JobList tests - rendering, status, errors, interactions (65.90% → 80%)`

---

### WU-4: App.tsx Tests Part 1 (3-4 hours)

**Current**: 47.50% → **Target**: 60% (intermediate)

**Uncovered Lines**: 34-40 (first batch)

**Test Cases Needed**:

```typescript
describe("App - Header & Branding", () => {
  it("should render ForgeSyte logo/branding");
  it("should apply ForgeSyte brand colors to header");
  it("should render navigation structure");
  it("should display title/app name");
});

describe("App - Navigation Structure", () => {
  it("should render stream mode button");
  it("should render upload mode button");
  it("should show correct active state for stream mode");
  it("should show correct active state for upload mode");
  it("should apply brand colors to active button");
});

describe("App - Initial State", () => {
  it("should render in stream mode by default");
  it("should initialize with correct component structure");
  it("should pass mode to child components");
});

describe("App - Props Passing", () => {
  it("should pass isConnected to children");
  it("should pass mode to children");
  it("should pass WebSocket state correctly");
});
```

**Mocks Required**:
```typescript
Mock useWebSocket hook
Mock child components (CameraPreview, JobList, etc.)
```

**Commit**: `test: Add App.tsx tests - header, navigation, props (47.50% → 60%)`

---

### WU-5: App.tsx Tests Part 2 (4-6 hours)

**Current**: 60% → **Target**: 80%+ (+20%)

**Uncovered Lines**: 65-71, 83, 271-274

**Test Cases Needed**:

```typescript
describe("App - Mode Switching", () => {
  it("should switch to stream mode when button clicked");
  it("should switch to upload mode when button clicked");
  it("should update child components on mode change");
  it("should clear previous mode data on switch");
});

describe("App - Stream Mode", () => {
  it("should display CameraPreview in stream mode");
  it("should display WebSocket status in stream mode");
  it("should hide JobList in stream mode");
  it("should show results panel in stream mode");
});

describe("App - Upload Mode", () => {
  it("should display upload control in upload mode");
  it("should hide CameraPreview in upload mode");
  it("should display JobList in upload mode");
  it("should show results panel in upload mode");
});

describe("App - WebSocket Integration", () => {
  it("should show connected state when isConnected=true");
  it("should show disconnected state when isConnected=false");
  it("should display connection status message");
  it("should disable controls when disconnected");
  it("should show reconnection message on disconnect");
});

describe("App - Error Handling", () => {
  it("should display error boundary on error");
  it("should show error message to user");
  it("should provide recovery mechanism");
});

describe("App - Results Display", () => {
  it("should show ResultsPanel when results available");
  it("should hide ResultsPanel when no results");
  it("should pass results data to ResultsPanel");
  it("should update results on new analysis");
});

describe("App - Plugin Selection", () => {
  it("should display PluginSelector");
  it("should pass selected plugin to WebSocket");
  it("should update plugin on user selection");
});
```

**Mocks Required**:
```typescript
Mock useWebSocket with various states (connected, disconnected, error)
Mock child components
Mock result data
Mock plugin list
```

**Commit**: `test: Complete App.tsx tests - mode switching, integration, errors (60% → 80%+)`

---

### WU-6: Coverage Finalization (1 hour)

**Current**: ~79-80% → **Target**: 80%+ confirmed

**Tasks**:
```bash
# Run full coverage report
npm run test:coverage

# Verify all components 80%+
npm run test:coverage 2>&1 | grep -E "%" | grep -v "100%"

# Run all tests
npm run test

# Verify no errors
npm run lint
npm run type-check
```

**Success Criteria**:
- [ ] All tests pass: `npm run test`
- [ ] Overall coverage ≥80%
- [ ] App.tsx ≥80%
- [ ] JobList.tsx ≥80%
- [ ] CameraPreview.tsx ≥80%
- [ ] No console errors

**Commit**: `test: Verify all components meet 80%+ coverage threshold`

---

## Git Workflow

```bash
# Start WU-2
git checkout -b test-coverage-camera-preview
# Add tests...
git add .
git commit -m "test: Add CameraPreview tests - device mgmt, lifecycle, capture"
git push origin test-coverage-camera-preview
git checkout main && git merge test-coverage-camera-preview && git push origin main

# Repeat for WU-3, WU-4, WU-5, WU-6 with appropriate branch names
```

---

## Timeline & Estimates

| WU | Task | Duration | Status |
|----|------|----------|--------|
| 1 | Coverage Setup | 45 min | ✅ DONE |
| 2 | CameraPreview tests | 2-3 hrs | TODO |
| 3 | JobList tests | 2-3 hrs | TODO |
| 4 | App.tsx tests (part 1) | 3-4 hrs | TODO |
| 5 | App.tsx tests (part 2) | 4-6 hrs | TODO |
| 6 | Finalization & verify | 1 hr | TODO |
| **TOTAL** | - | **13-18 hrs** | - |

---

## Key Files to Review Before Testing

1. **src/components/CameraPreview.tsx** - Lines 51-75, 91-108, 184-196
2. **src/components/JobList.tsx** - Lines 36-42, 60-62, 109-130
3. **src/App.tsx** - Lines 34-40, 65-71, 83, 271-274

```bash
# View uncovered sections
cat src/components/CameraPreview.tsx | sed -n '51,75p'
cat src/components/JobList.tsx | sed -n '36,42p'
cat src/App.tsx | sed -n '34,40p'
```

---

## Testing Best Practices

1. **Mock external dependencies**:
   - `navigator.mediaDevices` for camera
   - `useWebSocket` hook
   - API calls
   - Browser APIs

2. **One assertion per test** where possible

3. **Descriptive test names**:
   ```typescript
   // ✅ Good
   it("should show pending status badge for pending jobs");
   
   // ❌ Bad
   it("renders status");
   ```

4. **Test behavior, not styling**:
   ```typescript
   // ✅ Good - tests functionality
   expect(camera.play).toHaveBeenCalled();
   
   // ❌ Bad - tests CSS only
   expect(element).toHaveStyle("color: red");
   ```

5. **Run tests frequently**:
   ```bash
   npm run test              # After each test
   npm run test:coverage     # After completing a component
   ```

---

## Success Metrics

- [ ] WU-1: ✅ Baseline captured (77.14%)
- [ ] WU-2: CameraPreview to 80%+ (66.66% → 80%+)
- [ ] WU-3: JobList to 80%+ (65.90% → 80%+)
- [ ] WU-4: App.tsx intermediate (47.50% → 60%+)
- [ ] WU-5: App.tsx final (60% → 80%+)
- [ ] WU-6: Overall ≥80% verified
- [ ] All tests pass with no errors
- [ ] Merged to main branch

---

## Progress Tracking

**Main Files**:
- `docs/work-tracking/ISSUE_18_PROGRESS.md` - Update after each WU
- `docs/work-tracking/COVERAGE_BASELINE.md` - Reference baseline
- `web-ui/coverage-baseline.txt` - Raw baseline output (WU-1)

**Update Progress.md after each WU**:
- Start/end time
- Coverage % change
- Any blockers
- Commit message

---

## Related Issues

- Issue #18: WebUI Test Coverage (THIS ISSUE)
- Issue #17: WebSocket infinite reconnection (FIXED)
- Issue #19: Frame validation error (open)

---

## Quick Reference

```bash
# Run tests
npm run test

# Generate coverage report
npm run test:coverage

# Filter for uncovered files
npm run test:coverage 2>&1 | grep -E "^\s+src"

# View specific coverage
npm run test:coverage 2>&1 | grep -E "(App|JobList|CameraPreview)"

# Watch mode (helpful for development)
npm run test -- --watch

# Run single test file
npm run test src/components/App.test.tsx
```

---

**Baseline**: 77.14% overall (captured 2026-01-12)  
**Target**: 80%+ all components  
**Estimated Total Effort**: 13-18 hours  
**Ready to Begin**: WU-2 (CameraPreview tests)
