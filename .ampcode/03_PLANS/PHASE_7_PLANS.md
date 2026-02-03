# Phase 7: CSS Modules Migration Plan

**Status**: Ready to execute  
**Baseline**: Phase 6A (eef5ebf) — Clean, verified, 347 tests passing  
**Goal**: Migrate web-ui to CSS Modules with **zero runtime changes**  
**Timeline**: Estimated 6-8 PRs (1 per tier + 1 per critical component)  
**Risk Level**: LOW (CSS-only, strict guardrails)

---

## 1. Executive Overview

Phase 7 is a **pure presentation refactor** — no logic changes, no API changes, no test changes, no pipeline changes.

**What's changing:**
- Global/ad-hoc CSS → CSS Modules (local scoping, better maintainability)
- `className="foo bar"` → `className={clsx(styles.foo, styles.bar)}`
- One `.module.css` per component

**What's NOT changing:**
- Tests (347 passing → 347 passing)
- Hooks (`useVideoProcessor`, `useWebSocket`, etc.)
- API client (`client.ts`, `pollJob()`, etc.)
- Job pipeline behaviour
- Server code
- Any runtime logic

---

## 2. Guardrails (Non-Negotiable)

### Forbidden Files (Locked)
```
web-ui/src/hooks/useVideoProcessor.ts
web-ui/src/api/client.ts
web-ui/src/api/pollJob.ts
web-ui/src/hooks/useWebSocket.ts
```
**Do not edit.** If logic change needed → Escalate.

### Test Rules
- ✅ Same test count (347 tests)
- ✅ 2 APPROVED pre-Phase-7 skips (must remain)
- ❌ No new tests
- ❌ No deleted tests
- ❌ No `.skip`, `.only`, `xit`, `xdescribe`, `xtest` (except 2 APPROVED)
- ❌ No test file moves, renames, edits

### CSS Rules
- ✅ `.module.css` files (local scoping)
- ✅ `className={styles.foo}` (JSX)
- ✅ `clsx()` for multiple classes
- ❌ No `:global()` selectors
- ❌ No global CSS imports (except main index.css)
- ❌ No CSS resets in modules

### PR Scope
- 1 tier per PR (or 1-3 components max)
- CSS changes only (no prop refactors, no state changes, no hook changes)
- Must fit on one screen (reviewable diff)

---

## 3. Component Migration Tiers

### Tier 1 – Leaf Components (Low Risk)
**Estimated: 1 PR**

- [ ] RecordButton
- [ ] ConfidenceSlider
- [ ] OverlayToggles (simple toggles)
- [ ] JobStatusIndicator (status badges)
- [ ] ErrorMessage (error display)

**Why first:**
- No dependencies on other components
- Single responsibility
- Easy to test visually

**Files to update:**
- `RecordButton.tsx` → `RecordButton.module.css` + classname update
- `ConfidenceSlider.tsx` → `ConfidenceSlider.module.css` + classname update
- (etc.)

---

### Tier 2 – Mid-Level Layout (Medium Risk)
**Estimated: 2 PRs**

**Group 2A – Sidebar/Nav:**
- [ ] PluginSelector
- [ ] ToolSelector (if still exists)
- [ ] DeviceSelector
- [ ] Navigation wrapper

**Group 2B – Main panels:**
- [ ] UploadPanel / FileInput
- [ ] ResultsPanel
- [ ] JobList
- [ ] ConfigPanel

**Why second:**
- Moderate structural complexity
- Depend on Tier 1 components (may have styles applied)
- Still isolated from job logic

---

### Tier 3 – Page Level (Medium-High Risk)
**Estimated: 1-2 PRs**

- [ ] App.tsx (root layout)
- [ ] MainLayout / PageShell
- [ ] Page containers (if separate)

**Why third:**
- Layout-heavy
- Lots of conditional rendering
- Touch more of the component tree

---

### Tier 4 – Critical/Risky (High Risk)
**Estimated: 2-3 PRs**

- [ ] VideoTracker (job pipeline interaction)
- [ ] ResultOverlay (frame rendering, drawing)
- [ ] CameraPreview (video element)
- [ ] Any component directly consuming `job.result`

**Why last:**
- Touch job pipeline output
- Contain stateful logic
- Highest test coverage
- Any breaking change = test failure (catches early)

---

## 4. Execution Workflow

### Before First PR
```bash
# Verify baseline on Phase 6A
git checkout main
bash scripts/phase6/phase6_verify_baseline.sh
# Expected: 347 tests, lint clean, types clean

# Create Phase 7 branch
git checkout -b phase-7-css-modules
git reset --hard origin/main
```

### Per PR
```bash
# 1. Create feature branch for specific tier
git checkout -b phase-7/tier-1-buttons
# (or tier-2a, tier-2b, tier-3, tier-4, etc.)

# 2. Update 1-3 components
#    - Create ComponentName.module.css
#    - Update ComponentName.tsx classnames
#    - Update import statements
#    - Remove old global classnames (if any)

# 3. Run verification
npm test -- --run              # Should still be 347 tests
npm run lint                   # Should pass
npm run type-check             # Should pass
uv run pre-commit run --all-files

# 4. If all pass → commit + push
git add .
git commit -m "phase7(tier-1): Migrate Button + IconButton to CSS Modules

- Create Button.module.css with scoped styles
- Update Button.tsx to use styles.* classnames
- Remove global button-specific CSS from index.css

Tests: 347 passing (no changes)
Lint: Clean
Types: Clean"

git push -u origin phase-7/tier-1-buttons

# 5. Create PR (see PHASE_7_PR_TEMPLATE.md)

# 6. After merge
git checkout phase-7-css-modules
git pull origin phase-7-css-modules
git branch -d phase-7/tier-1-buttons
```

---

## 5. Risk Mitigation

### What Could Go Wrong

**Risk**: CSS scoping breaks styling  
**Mitigation**: Visual regression test (manual review of diffs)  
**Detection**: `npm test` would fail if component breaks

**Risk**: Missed old global classes  
**Mitigation**: Search for `className="old-name"` before commit  
**Detection**: Lint will catch unused classes

**Risk**: classname import forgotten  
**Mitigation**: Use TypeScript strict mode (catches missing imports)  
**Detection**: `npm run type-check` fails

**Risk**: Commit message doesn't justify test changes  
**Mitigation**: Pre-commit hook requires `TEST-CHANGE` if tests modified  
**Detection**: Commit fails

**Risk**: Logic change sneaks in  
**Mitigation**: PR reviewer checks diff is CSS-only  
**Detection**: `git diff` shows non-CSS changes

### Rollback Plan

If a PR breaks tests or causes regression:
```bash
# Option 1: Revert PR
git revert <commit-hash>
git push

# Option 2: Escalate (if ambiguous)
# Use PHASE_7_ESCALATION_TEMPLATE.md
```

---

## 6. Testing Strategy

### Per-PR Verification
```bash
npm test -- --run
# Expected: 347 passed | 2 skipped
# Any failures = STOP (investigate or rollback)

npm run lint
# Expected: 0 errors, 1 warning (pre-existing)

npm run type-check
# Expected: 0 errors

uv run pre-commit run --all-files
# Expected: All hooks pass (including web-ui tests)
```

### Full Baseline Verification (Before & After)
```bash
bash scripts/phase7/baseline-verify.sh
# Runs: Tests + Lint + Type-check + Pre-commit
```

### Skipped Tests Check
```bash
npx ts-node scripts/phase7/skipped-tests-check.ts
# Expected: Only 2 APPROVED pre-Phase-7 skips
# No new .skip or .only allowed
```

### Forbidden Files Check
```bash
npx ts-node scripts/phase7/forbidden-file-check.ts
# Expected: No changes to locked files
```

---

## 7. Component Priority (Recommended Order)

### PR 1: Tier 1A – Simple Components (1-2 days)
```
RecordButton, ConfidenceSlider, OverlayToggles
```
**Why**: Fastest, builds confidence

### PR 2: Tier 1B – More Leaf Components (1-2 days)
```
JobStatusIndicator, ErrorMessage, Badges
```

### PR 3: Tier 2A – Sidebar/Nav (2-3 days)
```
PluginSelector, ToolSelector, DeviceSelector
```

### PR 4: Tier 2B – Main Panels (2-3 days)
```
UploadPanel, ResultsPanel, JobList
```

### PR 5: Tier 3 – Page Layout (2-3 days)
```
App.tsx root layout, MainLayout
```

### PR 6: Tier 4A – Critical (2-3 days)
```
VideoTracker (highest risk, but tests will catch issues)
```

### PR 7: Tier 4B – Overlays (2-3 days)
```
ResultOverlay, CameraPreview
```

**Total Estimate**: 6-8 PRs, ~3-4 weeks (depending on review cycles)

---

## 8. Success Criteria

Phase 7 is complete when:

- ✅ All targeted components migrated to CSS Modules
- ✅ No regressions in job pipeline, upload, results, or streaming
- ✅ All tests passing (347 + 2 approved skips)
- ✅ Lint clean
- ✅ Types clean
- ✅ CI green on all PRs
- ✅ No changes to:
  - `useVideoProcessor.ts`
  - `client.ts`
  - Job polling logic
  - Test count or test content
- ✅ All `.only`, `.skip` removed except 2 APPROVED pre-Phase-7

---

## 9. Escalation Criteria

**STOP and escalate if:**

- ❌ Any test fails or changes
- ❌ Lint/type-check fails
- ❌ PR requires editing `useVideoProcessor`, `client.ts`, or job logic
- ❌ PR requires adding/removing/moving tests
- ❌ `npm test` doesn't run full 347 tests
- ❌ New `.skip` or `.only` appears in code
- ❌ Forbidden files are modified

**Escalation Process:**
1. Open `PHASE_7_ESCALATION_TEMPLATE.md`
2. Document the issue, attempted fix, blocker
3. Wait for review before proceeding

---

## 10. Documentation Links

- **Guardrails**: `PHASE_7_CSS_MODULES.md`
- **Component Checklist**: `PHASE_7_COMPONENT_CHECKLIST.md`
- **PR Template**: `PHASE_7_PR_TEMPLATE.md`
- **Escalation**: `PHASE_7_ESCALATION_TEMPLATE.md`
- **Verification Scripts**:
  - `scripts/phase7/baseline-verify.sh`
  - `scripts/phase7/forbidden-file-check.ts`
  - `scripts/phase7/skipped-tests-check.ts`

---

## 11. Sign-Off

**Phase 7 Ready to Execute**: ✅

- Baseline verified (Phase 6A, commit eef5ebf)
- Guardrails in place (pre-commit hooks, forbidden file checks)
- Tiers defined with priority order
- PR workflow documented
- Risk mitigation in place
- Rollback plan available

**Next Step**: Begin PR 1 (Tier 1A).
