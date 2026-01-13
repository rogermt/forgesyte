# Issue #18: Coverage Gap Analysis (Template)

**Status**: To be filled in after WU-1  
**Created**: 2026-01-12  

---

## How to Generate This Analysis

After running `npm run test:coverage` in WU-1, analyze the coverage report and fill in the sections below.

```bash
cd /home/rogermt/forgesyte/web-ui
npm run test:coverage 2>&1 | grep -A 100 "coverage"
```

The coverage output will show:
- `Statements` - % of code statements covered
- `Branches` - % of conditional branches covered
- `Functions` - % of functions called in tests
- `Lines` - % of lines of code executed in tests

---

## App.tsx Coverage Analysis

**Current Status**: TBD (expected ~33%)

### Coverage Breakdown
```
Statements: ??%
Branches:  ??%
Functions: ??%
Lines:     ??%
```

### Lines Missing Tests
```
[Run coverage report and list uncovered lines here]
```

### Uncovered Features
- [ ] Header rendering
- [ ] Navigation structure
- [ ] Mode switching (stream vs upload)
- [ ] WebSocket integration
- [ ] Error handling
- [ ] Conditional rendering
- [ ] Plugin selection UI
- [ ] Results panel display

### Tests Needed for WU-4
```
Target: 48-52% (intermediate)

Suggested test cases:
- Render ForgeSyte header/branding
- Render navigation tabs/buttons
- Apply ForgeSyte brand colors
- Switch between stream and upload modes
- Show correct layout for each mode
- Pass props to child components correctly
```

### Tests Needed for WU-5
```
Target: 80%+

Suggested test cases:
- Handle WebSocket connection state changes
- Update UI when WebSocket connects/disconnects
- Display error boundaries properly
- Render JobList when in upload mode
- Render CameraPreview when in stream mode
- Show results panel on successful analysis
- Handle plugin selection changes
```

---

## JobList.tsx Coverage Analysis

**Current Status**: TBD (expected ~65%)

### Coverage Breakdown
```
Statements: ??%
Branches:  ??%
Functions: ??%
Lines:     ??%
```

### Lines Missing Tests
```
[Run coverage report and list uncovered lines here]
```

### Uncovered Features
- [ ] Job status rendering
- [ ] Error message display
- [ ] Empty state
- [ ] Pagination/filtering
- [ ] Job selection
- [ ] Data refresh
- [ ] Loading states
- [ ] Status indicators

### Tests Needed for WU-2
```
Target: 72-75% (intermediate)

Suggested test cases:
- Render job list with multiple jobs
- Display correct status badge for each job (pending, processing, completed, failed)
- Show error message when provided
- Display empty state when no jobs
- Apply correct styling for each status
- Show loading indicator while fetching
```

### Tests Needed for WU-3
```
Target: 80%+

Suggested test cases:
- Handle job click/selection
- Update selected job when clicked
- Trigger job details panel
- Handle job deletion if applicable
- Refresh job list
- Implement pagination if applicable
- Filter/sort jobs if applicable
- Show estimated completion time if applicable
```

---

## CameraPreview.tsx Coverage Analysis

**Current Status**: TBD (expected ~45%, analyzed separately in CAMERAPREVIEW_TEST_COVERAGE_ANALYSIS.md)

**Note**: This component has detailed analysis already. If time permits, add tests from that analysis.

---

## Other Components to Check

### PluginSelector.tsx
```
Current Coverage: ??%
Target: 80%+
Status: TBD
```

### ResultsPanel.tsx
```
Current Coverage: ??%
Target: 80%+
Status: TBD
```

### Other Components
```
List any other components found below 80%:
- Component Name: ??% (gap: ??)
- Component Name: ??% (gap: ??)
```

---

## Coverage Baseline vs Target

| Component | Baseline | Target | Gap | WU |
|-----------|----------|--------|-----|-----|
| App.tsx | TBD | 80% | TBD | 4-5 |
| JobList.tsx | TBD | 80% | TBD | 2-3 |
| CameraPreview.tsx | TBD | 80% | TBD | Optional |
| PluginSelector.tsx | TBD | 80% | TBD | Optional |
| ResultsPanel.tsx | TBD | 80% | TBD | Optional |
| **OVERALL** | **TBD** | **80%** | **TBD** | - |

---

## How to Fill This In

1. Run coverage report: `npm run test:coverage`
2. For each component below 80%, note:
   - Current coverage %
   - Which lines/branches are uncovered
   - What features those lines implement
   - What tests would cover them

3. Prioritize by gap size:
   - Large gaps (>25%): High priority
   - Medium gaps (10-25%): Medium priority
   - Small gaps (<10%): Low priority

4. Use the coverage report output format:
   ```
   ----------|----------|----------|----------|----------|--------|
   File      | Stmts    | Branch   | Funcs    | Lines    | Uncovered Lines
   ----------|----------|----------|----------|----------|--------|
   app/App.tsx | 45/120 | 12/35  | 8/12   | 46/122 | 54,67,89-95,105
   ```

---

## Notes

- Fill in this document after WU-1 coverage baseline is captured
- Use this as the authoritative reference for what tests to write in WU-2 through WU-6
- Update this document if coverage patterns change unexpectedly
- Link to specific code locations when possible (e.g., "Line 54-67 in App.tsx for error handling")

---

**To Be Completed In**: WU-1 (Coverage Setup)
**Owner**: Agent working on Issue #18
**Updated**: [Timestamp of WU-1 completion]
