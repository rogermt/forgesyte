# Phase 7 – PR Checklist

Use this checklist for **every Phase 7 PR** before opening it for review.

---

## Pre‑PR Steps

- [ ] Code changes reviewed locally
- [ ] Styling looks correct (visual inspection)
- [ ] Component tier confirmed (check `PHASE_7_COMPONENT_CHECKLIST.md`)

---

## Guardrails Verification

- [ ] No changes to `web-ui/src/hooks/useVideoProcessor.ts`
- [ ] No changes to `web-ui/src/api/client.ts`
- [ ] No changes to job polling logic
- [ ] No changes to Phase 6 test files
- [ ] No new tests added
- [ ] No tests removed
- [ ] No skipped tests (`it.skip`, `describe.skip`, `.only()`, etc.)
- [ ] No server-side changes

---

## Quality Gates (Must Pass)

### Tests
```bash
cd web-ui && npm test -- --run
```
- [ ] Result: `Tests  8 passed` (or current count, unchanged)

### Linting
```bash
cd web-ui && npm run lint
```
- [ ] No errors (warnings acceptable if documented)

### Type Checking
```bash
cd web-ui && npm run type-check
```
- [ ] No TypeScript errors

### Pre-Commit Hooks
```bash
cd .. && uv run pre-commit run --all-files
```
- [ ] All 7 hooks pass:
  - [ ] black
  - [ ] ruff
  - [ ] mypy
  - [ ] web-ui-lint
  - [ ] web-ui-tests
  - [ ] detect-unapproved-skipped-tests
  - [ ] prevent-test-changes-without-justification

---

## Component Checklist

- [ ] Imported CSS module: `import styles from './ComponentName.module.css';`
- [ ] Updated `className` references to use `styles.*`
- [ ] Removed old global/inline class names (if applicable)
- [ ] CSS module follows naming convention: `ComponentName.module.css`
- [ ] No global selectors in CSS module (no `body`, `html`, `*`)
- [ ] No `:global` unless explicitly documented

---

## Documentation Updates

- [ ] `PHASE_7_COMPONENT_CHECKLIST.md` updated with component status
- [ ] If escalation was needed: `PHASE_7_ESCALATION_TEMPLATE.md` filled in PR description

---

## Edge Cases

- [ ] If component uses `clsx()` or class merging, verified it still works
- [ ] If component has theme variants, CSS module handles all of them
- [ ] If component is responsive, media queries preserved correctly

---

## PR Description Template

When opening the PR, include:

```markdown
## Phase 7 – CSS Modules Migration

**Components:** [Component 1, Component 2, ...]
**Tier:** [Tier 1/2/3/4]

### Changes
- Migrated [Component] to CSS Modules
- Removed global class references
- Updated className bindings

### Testing
- [x] `npm test -- --run` (8/8 passed)
- [x] `npm run lint` (clean)
- [x] `npm run type-check` (clean)
- [x] `uv run pre-commit run --all-files` (all 7 hooks pass)

### Guardrails
- [x] No changes to `useVideoProcessor`
- [x] No changes to `client.ts`
- [x] No new/removed tests
- [x] No skipped tests
```

If escalation was needed, add section:

```markdown
## Phase 7 Escalation

See: PHASE_7_ESCALATION_TEMPLATE.md (filled in below)

[Escalation details...]
```

---

## Final Checks

- [ ] Branch name follows convention: `feature/phase7-*` or `refactor/phase7-*`
- [ ] Commit message is clear and describes CSS changes
- [ ] No unintended files in commit (check `git status`)
- [ ] PR is linked to Milestone 7 issue (if applicable)

---

**Status:** Ready to open PR ✅
