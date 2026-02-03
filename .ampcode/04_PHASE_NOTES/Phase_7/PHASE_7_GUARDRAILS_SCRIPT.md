# Phase 7 – Guardrails Script (Reference)

This describes the checks that should run locally or in CI to enforce Phase 7 rules.

---

## Forbidden File Changes

These files **must not be modified** in any Phase 7 PR:

- `web-ui/src/hooks/useVideoProcessor.ts`
- `web-ui/src/api/client.ts`
- `web-ui/src/api/client.test.ts`
- `web-ui/src/hooks/__tests__/useVideoProcessor.test.ts`
- `web-ui/src/components/__tests__/VideoTracker.test.tsx`
- Any job polling helpers
- Server-side files

**Detection:**
```bash
git diff --name-only | grep -E \
  "useVideoProcessor\.ts$|client\.ts$|server/|__tests__.*test\.tsx?$"
```

If any match, the PR should be blocked or escalated.

---

## Skipped Tests Detection

Scan for patterns indicating skipped/isolated tests:

- `it.skip`
- `describe.skip`
- `test.skip`
- `xit`
- `xdescribe`
- `xtest`
- `.skip(`
- `.only(`

**Detection:**
```bash
git diff --cached -U0 | grep -E "\.skip\(|\.only\(|xit|xdescribe"
```

Any occurrence should fail the check. Exception: If `// APPROVED: <reason>` appears on the same line, allow it (and log it).

---

## Test Count Verification

Before and after each Phase 7 PR, test count **must not change**:

```bash
cd web-ui
npm test -- --run 2>&1 | grep "Tests.*passed"
# Should show: Tests  8 passed
```

If the count changes, the PR is not Phase 7 compliant.

---

## Baseline Commands

Before first Phase 7 PR and after each PR:

```bash
cd web-ui
npm test -- --run              # Must show 8 tests passed
npm run lint                   # Must pass (no errors)
npm run type-check             # Must pass
cd ..
uv run pre-commit run --all-files  # All 7 hooks must pass
```

If any fail, the PR cannot be merged.

---

## CSS Modules Conventions Check

- File naming: `ComponentName.module.css` next to `ComponentName.tsx`
- Import pattern: `import styles from './ComponentName.module.css';`
- Usage: `className={styles.root}` or `className={clsx(styles.root, styles.active)}`
- No global selectors (body, html, *, global tag selectors)
- No `:global` without explicit justification

**Manual review required** – linter won't catch all of these.

---

## Phase 7 PR Checklist Template

Every Phase 7 PR must include:

```markdown
## Phase 7 Compliance

- [ ] Only CSS Modules changes (no logic changes)
- [ ] No changes to `useVideoProcessor`
- [ ] No changes to `client.ts`
- [ ] No changes to job polling
- [ ] No changes to Phase 6 tests
- [ ] No new tests, no removed tests
- [ ] No skipped tests
- [ ] `npm test -- --run` passes (8/8)
- [ ] `npm run lint` passes
- [ ] `npm run type-check` passes
- [ ] `uv run pre-commit run --all-files` passes
```

---

## Escalation Workflow

If a Phase 7 PR needs to change anything beyond CSS, it **must**:

1. Use the `PHASE_7_ESCALATION_TEMPLATE.md`
2. Clearly label it: "Phase 7 Escalation – Logic Change Request"
3. Explain why the change is necessary
4. Document risk and mitigations
5. Get explicit approval before merging

---

## CI Integration (Future)

These checks can be automated in GitHub Actions:

```yaml
# Pseudo-code
- name: "Phase 7 – Check forbidden files"
  if: github.base_ref == 'main' && contains(github.head_ref, 'phase-7')
  run: |
    git diff origin/main --name-only | grep -E "useVideoProcessor|client\.ts|__tests__"
    if [ $? -eq 0 ]; then exit 1; fi

- name: "Phase 7 – Check for skipped tests"
  run: git diff origin/main -U0 | grep -E "\.skip\(|\.only\(" && exit 1 || true

- name: "Phase 7 – Verify test count unchanged"
  run: |
    cd web-ui
    npm test -- --run 2>&1 | grep -q "Tests  8 passed"
```
