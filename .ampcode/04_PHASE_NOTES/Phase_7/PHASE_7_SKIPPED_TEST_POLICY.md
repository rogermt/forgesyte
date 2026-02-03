# Phase 7 — Skipped Test Approval Policy

During Phase 7 (CSS Modules Migration), **skipped tests are strictly forbidden** unless they meet all of the following criteria:

---

## ✅ Allowed Skipped Tests (Only 2 Cases)

### **Case 1 — Pre‑existing skipped tests**
A test that was already skipped *before* Phase 7 began.

These must be explicitly acknowledged with:

```ts
// APPROVED: Pre-Phase-7 skip — <reason>
```

Valid reasons include:
- CI environment limitations (e.g., plugin sync)
- jsdom limitations (e.g., image loading)
- Known non‑Phase‑7 constraints

---

### **Case 2 — Explicitly escalated and approved**
If a test must be skipped due to a real technical blocker, the dev must:

1. Add a PR section titled:  
   **“Phase 7 Escalation – Logic/Test Change Request”**
2. Fill out the escalation template  
3. Wait for approval before merging

---

## ❌ Forbidden Skipped Tests

The following are **not allowed**:

- Adding new `.skip` during Phase 7  
- Leaving `.skip` without an APPROVED comment  
- Removing tests  
- Rewriting tests to avoid failures  
- Using `.only` or `.skip` to bypass failures  
- Silent skips with no justification  

---

## Required Format

Every approved skip must follow this exact pattern:

```ts
it.skip("...", async () => {  
  // APPROVED: Pre-Phase-7 skip — <reason>
```

Or:

```ts
it.skip("...", () => {  
  // APPROVED: Escalation approved — <reason>
```

The comment must include:
- The word **APPROVED**
- The phrase **Pre-Phase-7** or **Escalation approved**
- A short reason

---

## CI Enforcement

CI will fail if:

- A `.skip` exists without an APPROVED comment  
- A `.only` exists anywhere  
- A new skipped test is added  
- A skipped test is modified without approval  

---

## Summary

Phase 7 is a **CSS‑only migration**.  
Skipped tests must be **explicit**, **intentional**, and **documented**.

No silent skips.  
No ignored guardrails.  
No exceptions.
