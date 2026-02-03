# Phase 7 – Escalation Template

Use this template **whenever a Phase 7 CSS Modules change requires touching anything outside styling**.

Copy this into the PR description under a heading like:

> Phase 7 Escalation – Logic Change Request

---

## 1. Context

**Component(s):**

- e.g. `VideoTracker`, `Header`, `UploadPage`

**Tier:**

- Tier 1 / Tier 2 / Tier 3 / Tier 4

**Related Issue / Milestone:**

- e.g. Milestone 8 – Phase 7 CSS Modules Migration

---

## 2. Proposed Change

**Describe the change that goes beyond pure styling:**

- What file(s) need logic changes?
- Why can't this be done as CSS‑only?
- What behaviour will change (if any)?

---

## 3. Guardrails Impacted

Tick any that are affected:

- [ ] `useVideoProcessor` must not change
- [ ] `client.ts` must not change
- [ ] Job polling behaviour must not change
- [ ] Phase 6 tests must not change
- [ ] No new tests / no removed tests
- [ ] No skipped tests
- [ ] No server / API changes

For each checked item, explain why:

> **Explanation:**

---

## 4. Risk Assessment

- **Risk level:** Low / Medium / High
- **Potential regressions:**
  - e.g. Video playback, job status display, error handling
- **Mitigations:**
  - e.g. Additional manual testing, temporary feature flag, extra logging

---

## 5. Testing Plan

- [ ] `npm test -- --run`
- [ ] `npm run lint`
- [ ] `npm run type-check`
- [ ] `uv run pre-commit run --all-files`
- [ ] Manual UI verification (describe scenarios)

---

## 6. Decision

- **Approved by:**  
- **Date:**  
- **Conditions / Follow‑ups:**

> e.g. "Approved provided no new props are added to VideoTracker and all tests remain unchanged."
