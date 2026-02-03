# Phase 7 – CSS Modules & UI Hardening

This file is the **entry point** for all Phase 7 work.  
Detailed, long‑form notes are split across multiple files to keep them LLM‑friendly.

---

## 1. Purpose

Phase 7 focuses on:

- Migrating web‑ui components to **CSS Modules**
- Preserving the **Phase 6 job pipeline** and API contracts
- Enforcing **strict guardrails** around core logic
- Providing a **clear, incremental migration path** for the dev

---

## 2. Key Documents

- `PHASE_7_CSS_MODULES.md` – migration strategy and guardrails
- `PHASE_7_COMPONENT_CHECKLIST.md` – component‑level tracking
- `PHASE_7_ESCALATION_TEMPLATE.md` – how to request logic changes
- `PHASE_7_GUARDRAILS_SCRIPT.md` – checks to enforce Phase 7 rules
- `PHASE_7_PR_CHECKLIST.md` – what to verify before opening a PR
- `PHASE_7_PR_TEMPLATE.md` – standard PR structure
- `01_NOTES.md` → `05_NOTES.md` – long‑form notes to dev (recovered from prior sessions)

---

## 3. Guardrails (Summary)

- No changes to:
  - `useVideoProcessor`
  - `client.ts`
  - Job polling logic
  - Phase 6 tests
- No new tests, no removed tests
- No skipped tests
- No server / API changes
- CSS‑only changes unless escalation is explicitly approved

See `PHASE_7_CSS_MODULES.md` for full details.

---

## 4. Execution Order

1. Confirm Phase 6 baseline is green (tests, lint, type‑check, pre‑commit)
2. Start with Tier 1 components (leaf components)
3. Move to Tier 2, then Tier 3
4. Only then touch Tier 4 (VideoTracker and related)
5. Use the escalation template if any logic change is required

---

## 5. Notes to Developer

Long‑form, conversational guidance is split into:

- `01_NOTES.md`
- `02_NOTES.md`
- `03_NOTES.md`
- `04_NOTES.md`
- `05_NOTES.md`

These contain the detailed reasoning, pitfalls, and historical context recovered from earlier conversations.

---

## 6. Quick Start

```bash
# Verify Phase 6 baseline
cd web-ui && npm test -- --run
npm run lint
npm run type-check
cd .. && uv run pre-commit run --all-files

# Read the docs
cat .ampcode/04_PHASE_NOTES/Phase_7/PHASE_7_CSS_MODULES.md
cat .ampcode/04_PHASE_NOTES/Phase_7/PHASE_7_COMPONENT_CHECKLIST.md

# Pick a Tier 1 component
# Create ComponentName.module.css next to ComponentName.tsx
# Update className references
# Test again
```

---

**Status:** Ready for Phase 7 execution  
**Date Created:** 2026-02-02  
**Phase 6 Baseline:** ✅ 8/8 tests passing
