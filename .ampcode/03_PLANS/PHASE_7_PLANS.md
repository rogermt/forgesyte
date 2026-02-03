# Phase 7: CSS Modules Migration – Execution Plan

**Status**: Ready for approval and execution  
**Baseline**: Phase 6A (eef5ebf) — 347 tests passing, verified clean  
**Goal**: Migrate web-ui to CSS Modules (pure presentation refactor, zero runtime changes)  
**Documentation**: Complete (see references below)

---

## 1. What Phase 7 Is

A **CSS Modules migration** — converting components from ad-hoc/global styling to scoped CSS Modules.

**What changes:** Styling approach only
- `className="foo bar"` → `className={clsx(styles.foo, styles.bar)}`
- `ComponentName.tsx` + new `ComponentName.module.css`
- No logic changes, no test changes, no API changes

**What stays frozen:**
- `useVideoProcessor.ts` (core hook)
- `client.ts` (API client)
- Job polling logic
- Phase 6 test files (all 347 tests, 2 APPROVED skips)
- Any Phase 6 test changes require `TEST-CHANGE` in commit message

---

## 2. Guardrails (Enforced)

**FORBIDDEN file changes** (locked):
- `web-ui/src/hooks/useVideoProcessor.ts`
- `web-ui/src/api/client.ts`
- `web-ui/src/hooks/__tests__/useVideoProcessor.test.ts`
- `web-ui/src/components/__tests__/VideoTracker.test.tsx`
- `web-ui/src/components/VideoTracker.tsx`
- Any Phase 6 test files

**Test rules:**
- No new tests
- No deleted tests
- No skipped tests (except 2 APPROVED pre-Phase-7 skips)
- No `.skip`, `.only`, `xit`, `xdescribe`, `xtest` (unless `// APPROVED: reason`)

**Quality gates (all PRs must pass):**
```bash
npm test -- --run                    # Expected: 347 passed | 2 skipped
npm run lint                         # Expected: 0 errors
npm run type-check                   # Expected: 0 errors
uv run pre-commit run --all-files    # Expected: All 7 hooks pass
```

---

## 3. Component Tiers (from PHASE_7_COMPONENT_CHECKLIST.md)

### Tier 1 – Leaf Components
Simple buttons, badges, wrappers — no dependencies on complex layouts
- [ ] Button, IconButton, Tag, Badge
- [ ] Spinner, Loader, Card, Panel
- [ ] FormField, Input, Select
- [ ] Example: `RecordButton`

### Tier 2 – Mid-Level Layout
Header, sidebar, nav, panels — structural components
- [ ] Header, Sidebar, Navigation, NavLinks
- [ ] MainLayout, Shell, Toolbar
- [ ] StatusBar, Footer, Modal, Dialog

### Tier 3 – Page Level
Dashboard, upload, results pages
- [ ] DashboardPage, UploadPage, ResultsPage, SettingsPage
- [ ] JobsList, HistoryView

### Tier 4 – Critical (High Risk)
Components touching job pipeline output
- [ ] VideoTracker, VideoControls
- [ ] Timeline, Scrubber
- [ ] Overlays (players, ball, pitch, radar)
- [ ] Any component consuming `job.result`

---

## 4. PR Workflow

### For Each Component Migration:

1. **Create feature branch**
   ```bash
   git checkout -b phase-7/tier-1-buttons
   # (or tier-2a, tier-3, tier-4, etc.)
   ```

2. **Create CSS Module**
   ```bash
   # Beside ComponentName.tsx, create:
   ComponentName.module.css
   ```

3. **Update component TSX**
   ```tsx
   import styles from './ComponentName.module.css';
   
   // Replace: className="foo bar"
   // With: className={clsx(styles.foo, styles.bar)}
   ```

4. **Run verification**
   ```bash
   npm test -- --run           # All 347 + 2 skips still passing?
   npm run lint
   npm run type-check
   uv run pre-commit run --all-files
   ```

5. **Commit (no TEST-CHANGE needed, CSS-only)**
   ```bash
   git commit -m "phase7: Migrate Button to CSS Modules
   
   - Create Button.module.css with scoped styles
   - Update className references to use styles.*
   - Remove old global button styles"
   ```

6. **Update tracking**
   - Mark component as `[x]` in `PHASE_7_COMPONENT_CHECKLIST.md`

7. **Open PR**
   - Use template: `PHASE_7_PR_TEMPLATE.md`
   - Title: `phase7: Migrate [Component] to CSS Modules`
   - Include: Test results, guardrails checklist, component tier

---

## 5. Escalation Process

**If you need to change forbidden files or tests:**

1. Use: `PHASE_7_ESCALATION_TEMPLATE.md`
2. Add to PR description under: "Phase 7 Escalation – Logic Change Request"
3. Explain why, document risk, propose mitigations
4. Wait for approval before merging
5. If approved, update commit message to include reason

---

## 6. Scripts (Run Before Each PR)

### Quick Check
```bash
# Verify baseline
bash scripts/phase7/baseline-verify.sh

# Check forbidden files
npx ts-node scripts/phase7/forbidden-file-check.ts

# Check skipped tests
npx ts-node scripts/phase7/skipped-tests-check.ts
```

### Combined Check (All at Once)
```bash
bash scripts/phase7/pr-guardrail.sh
# Runs all 3 checks + full baseline verification
```

---

## 7. Important Docs (Read Before Starting)

1. **PHASE_7_CSS_MODULES.md** – Full migration strategy
2. **PHASE_7_COMPONENT_CHECKLIST.md** – Tracks which components are done
3. **PHASE_7_PR_CHECKLIST.md** – What to verify before opening PR
4. **PHASE_7_PR_TEMPLATE.md** – PR description template
5. **PHASE_7_ESCALATION_TEMPLATE.md** – For logic changes (if needed)
6. **PHASE_7_SKIPPED_TEST_POLICY.md** – Rules for test skips
7. **PHASE_7_GUARDRAILS_SCRIPT.md** – Reference for guard checks
8. **PHASE_7_BASELINE_VERIFY.md** – Baseline verification details

---

## 8. Success Criteria

Phase 7 is complete when:
- ✅ All targeted components migrated to CSS Modules
- ✅ No regressions in job pipeline, upload, results, streaming
- ✅ All tests passing (347 + 2 approved skips)
- ✅ Lint clean, types clean, pre-commit green
- ✅ No changes to `useVideoProcessor`, `client.ts`, Phase 6 tests
- ✅ All `.only` and `.skip` removed except 2 APPROVED pre-Phase-7

---

## 9. Failure Modes (Stop & Escalate If)

- ❌ Test count changes
- ❌ Forbidden file is edited
- ❌ New `.skip` or `.only` appears without `// APPROVED:`
- ❌ Lint/type-check fails
- ❌ Pre-commit hooks fail
- ❌ Need to edit `useVideoProcessor` or `client.ts`

**Action**: Stop, escalate using `PHASE_7_ESCALATION_TEMPLATE.md`

---

## 10. Ready to Start?

**Before first PR:**
1. Read `PHASE_7_CSS_MODULES.md` and `PHASE_7_COMPONENT_CHECKLIST.md`
2. Run: `bash scripts/phase7/baseline-verify.sh` (confirm Phase 6A is clean)
3. Pick Tier 1 component (e.g., `RecordButton`)
4. Create branch: `git checkout -b phase-7/tier-1-buttons`

**Questions for approval:**
- Should we start with Tier 1? (Recommended: yes)
- Which component first? (Recommend: `RecordButton`)
- Timeline estimate per tier? (You decide)
- Any components we should skip or prioritize differently?

**I'm ready to:**
- Execute first PR (build CSS Module, update component, verify tests)
- Run verification scripts
- Commit and push
- Open PR with full checklist

**You decide:** What's the first task?

---

**Last note:** I'm not making up timelines, deadlines, or component priorities. All decisions are yours to approve. I will only execute what you explicitly approve.
