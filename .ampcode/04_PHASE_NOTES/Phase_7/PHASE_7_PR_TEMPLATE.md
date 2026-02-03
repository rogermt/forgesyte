# Phase 7 – Standard PR Template

Copy this template into the PR description when opening a Phase 7 CSS Modules PR.

---

## Phase 7 – CSS Modules Migration

**Components Migrated:**

- [ ] List component(s) here, e.g.:
  - `Button`
  - `Header`
  - `Sidebar`

**Tier:**

- Tier 1 / Tier 2 / Tier 3 / Tier 4 *(pick one)*

**Related Milestone:**

- Milestone 7 – Phase 7: CSS Modules Migration

---

## Summary

Describe what CSS Modules work was done:

- Migrated `ComponentName` to CSS Modules
- Created `ComponentName.module.css`
- Updated className references
- Removed old global styles (if applicable)

---

## Changes

**Files modified:**

- `web-ui/src/components/ComponentName.tsx`
- `web-ui/src/components/ComponentName.module.css` (new)

---

## Guardrails Compliance

*Check all:*

- [ ] No changes to `useVideoProcessor`
- [ ] No changes to `client.ts`
- [ ] No changes to job polling logic
- [ ] No changes to Phase 6 tests
- [ ] No new tests added
- [ ] No tests removed
- [ ] No skipped tests
- [ ] No server / API changes

---

## Testing

### Command Results

```bash
cd web-ui && npm test -- --run
# Expected: Tests  8 passed

npm run lint
# Expected: No errors (warnings OK with documentation)

npm run type-check
# Expected: 0 errors

cd .. && uv run pre-commit run --all-files
# Expected: All 7 hooks pass
```

**Results:**

- [ ] `npm test -- --run` ✅
- [ ] `npm run lint` ✅
- [ ] `npm run type-check` ✅
- [ ] `uv run pre-commit run --all-files` ✅ (7/7 hooks)

### Manual Testing

- [ ] Component renders correctly
- [ ] Styling matches design (visual inspection)
- [ ] No layout regressions
- [ ] Responsive design preserved (if applicable)

---

## Documentation

- [ ] `PHASE_7_COMPONENT_CHECKLIST.md` updated with component status
- [ ] CSS conventions followed (no global selectors, correct module naming)

---

## Escalation (if needed)

**If this PR touches anything beyond CSS Modules, check here:**

- [ ] Escalation template included below

### Phase 7 Escalation – Logic Change Request

*(Complete only if logic changes were required; otherwise delete this section.)*

**Component(s):**

- [List components requiring logic changes]

**Tier:**

- Tier 1 / 2 / 3 / 4

**Proposed Change:**

[Describe the change that goes beyond CSS styling]

**Guardrails Impacted:**

- [ ] `useVideoProcessor` affected
- [ ] `client.ts` affected
- [ ] Job polling logic affected
- [ ] Phase 6 tests affected
- [ ] Test count changed
- [ ] New tests added
- [ ] Skipped tests added
- [ ] Server / API changes

**For each checked item, explain why:**

> [Explanation]

**Risk Assessment:**

- Risk level: Low / Medium / High
- Potential regressions: [List]
- Mitigations: [List]

**Testing Plan:**

- [ ] `npm test -- --run`
- [ ] `npm run lint`
- [ ] `npm run type-check`
- [ ] `uv run pre-commit run --all-files`
- [ ] Manual verification (describe)

**Approval:**

- Approved by: [@person]
- Date: [Date]
- Conditions: [Any conditions/follow-ups]

---

## Checklist

Before merging:

- [ ] All guardrails checks passed
- [ ] All tests passing (8/8)
- [ ] All linting/typing clean
- [ ] Pre-commit hooks green
- [ ] Code review approved
- [ ] No blocking comments
- [ ] Escalation (if applicable) approved

---

**PR Author:** [Your name]  
**Date Created:** [Date]
