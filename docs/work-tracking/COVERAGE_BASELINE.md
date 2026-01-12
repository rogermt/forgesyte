# WebUI Test Coverage Baseline - 2026-01-12

**Captured**: 2026-01-12 19:55 UTC  
**Coverage Tool**: vitest v4.0.17 with v8 provider  
**Overall**: 77.14% statements (BELOW 80% TARGET)

---

## Coverage Summary by Component

| File | Statements | Branch | Functions | Lines | Target |
|------|-----------|--------|-----------|-------|--------|
| **All files** | **77.14%** | 77.33% | 74.24% | 77.99% | **80%** |
| App.tsx | 47.50% | 73.21% | 45.45% | 48.71% | 80% (+32.5%) |
| api/client.ts | 97.87% | 87.87% | 100% | 97.87% | ✅ PASS |
| components/CameraPreview.tsx | 66.66% | 63.82% | 60% | 69.84% | 80% (+13.34%) |
| components/JobList.tsx | 65.90% | 61.11% | 66.66% | 65.90% | 80% (+14.1%) |
| components/PluginSelector.tsx | 95.45% | 95.23% | 83.33% | 95.23% | ✅ PASS |
| components/ResultsPanel.tsx | 100% | 100% | 100% | 100% | ✅ PASS |
| hooks/useWebSocket.ts | 87.23% | 81.57% | 92.85% | 87.09% | ✅ PASS |

---

## Components Below 80% (Need Work)

### 1. App.tsx - **47.50%** (Lowest Priority)
**Gap**: +32.5% (CRITICAL)  
**Uncovered Lines**: 34-40, 65-71, 83, 271-274

**Current Coverage**: 
- Statements: 47.50%
- Branches: 73.21% (actually decent)
- Functions: 45.45%
- Lines: 48.71%

**Likely Gaps**:
- Mode switching logic (stream vs upload)
- WebSocket integration and error handling
- Conditional rendering of panels
- Props passing to child components

### 2. JobList.tsx - **65.90%**
**Gap**: +14.1%  
**Uncovered Lines**: 36-42, 60-62, 109-130

**Current Coverage**:
- Statements: 65.90%
- Branches: 61.11% (weak)
- Functions: 66.66%
- Lines: 65.90%

**Likely Gaps**:
- Job list rendering edge cases
- Error handling
- Job interactions (click, select)
- Status rendering variations

### 3. CameraPreview.tsx - **66.66%**
**Gap**: +13.34%  
**Uncovered Lines**: 51-75, 91-108, 184-196

**Current Coverage**:
- Statements: 66.66%
- Branches: 63.82% (weak)
- Functions: 60% (lowest)
- Lines: 69.84%

**Likely Gaps**:
- Camera lifecycle (start/stop)
- Frame capture logic
- Device enumeration
- Error handling for media access

---

## Components Already Passing 80%

### ✅ ResultsPanel.tsx - **100%**
Perfect coverage - no work needed.

### ✅ PluginSelector.tsx - **95.45%**
Nearly perfect - could add tests for edge cases (line 71).

### ✅ useWebSocket.ts - **87.23%**
Good coverage - could improve to 90%+ (uncovered lines 81-183, 209-211).

### ✅ client.ts - **97.87%**
Excellent - only missing line 103.

---

## Work Priority

### Critical (MUST DO)
1. **App.tsx** - 47.50% → 80% (+32.5%)
   - Highest gap
   - Most critical component
   - Blocks overall coverage

### High Priority (SHOULD DO)
2. **JobList.tsx** - 65.90% → 80% (+14.1%)
3. **CameraPreview.tsx** - 66.66% → 80% (+13.34%)

### Nice to Have (Optional)
4. **useWebSocket.ts** - 87.23% → 90%+ (optimization)
5. **PluginSelector.tsx** - 95.45% → 100% (optimization)

---

## Estimated Effort to Reach 80% Overall

| Component | Current | Target | Effort | WU |
|-----------|---------|--------|--------|-----|
| App.tsx | 47.50% | 80% | 8-10 hrs | 3-4 WUs |
| JobList.tsx | 65.90% | 80% | 2-3 hrs | 1-2 WUs |
| CameraPreview.tsx | 66.66% | 80% | 2-3 hrs | 1-2 WUs |
| **TOTAL** | **77.14%** | **80%** | **12-16 hrs** | **5-8 WUs** |

---

## Breakdown by Work Unit

### WU-1: Coverage Setup (DONE ✅)
- Installed @vitest/coverage-v8
- Captured baseline (this file)
- Analyzed coverage gaps

**Commit**: `chore: Setup coverage tools and capture baseline`

### WU-2: CameraPreview.tsx Tests (2-3 hours)
**Target**: 66.66% → 80% (+13.34%)

Priority:
- Device enumeration tests
- Camera start/stop lifecycle tests
- Frame capture tests
- Error handling tests

### WU-3: JobList.tsx Tests (2-3 hours)
**Target**: 65.90% → 80% (+14.1%)

Priority:
- Job rendering tests
- Status badge tests
- Error display tests
- Job interactions tests

### WU-4: App.tsx Tests Part 1 (3-4 hours)
**Target**: 47.50% → 65% (intermediate)

Focus:
- Header rendering
- Navigation structure
- Mode switching (basic)
- Props passing to children

### WU-5: App.tsx Tests Part 2 (4-6 hours)
**Target**: 65% → 80%+ (+15%)

Focus:
- WebSocket integration
- Error boundary behavior
- Conditional rendering (stream vs upload)
- Results panel integration

### WU-6: Coverage Optimization (Optional, 1-2 hours)
- Push useWebSocket.ts to 90%+
- Push PluginSelector.tsx to 100%

### WU-7: Final Verification (30 min)
- Confirm all components 80%+
- Run full test suite
- Merge to main

---

## Test File Locations

```
web-ui/src/
├── App.test.tsx               (27 tests)
├── App.integration.test.tsx   (11 tests)
├── api/
│   └── client.test.ts         (15 tests) ✅
├── components/
│   ├── CameraPreview.test.tsx (7 tests)  ❌ 66.66%
│   ├── JobList.test.tsx       (7 tests)  ❌ 65.90%
│   ├── PluginSelector.test.tsx (8 tests) ✅ 95.45%
│   └── ResultsPanel.test.tsx  (10 tests) ✅ 100%
├── hooks/
│   └── useWebSocket.test.ts   (17 tests) ✅ 87.23%
└── integration/
    └── server-api.integration.test.ts (18 tests)
```

---

## Next Steps (WU-2 and beyond)

1. **Read uncovered lines** in each component using source code
2. **Identify missing test cases** from coverage gaps
3. **Write focused tests** for uncovered functionality
4. **Run coverage frequently** to track progress
5. **Commit per WU** with descriptive messages

---

## Success Criteria

- [ ] App.tsx: ≥80% statements
- [ ] JobList.tsx: ≥80% statements
- [ ] CameraPreview.tsx: ≥80% statements
- [ ] Overall: ≥80% statements
- [ ] All tests pass: `npm run test`
- [ ] No console errors/warnings
- [ ] Merged to main

---

**Baseline Captured**: 2026-01-12 19:55 UTC  
**Ready for**: WU-2 (CameraPreview tests)  
**Total Estimated Effort**: 12-16 hours across 7 work units
