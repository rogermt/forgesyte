Absolutely, Roger.  
I’ll give you a **fully‑formed, developer‑ready, zero‑ambiguity HANDOVER.md** that you can paste directly into a new chat with your dev to begin Phase 7.

This is written in a **professional, authoritative, engineering‑lead voice**, and it assumes the dev is joining fresh, with no context from our conversations.  
It gives them **everything they need**, in the correct order, with no room for misinterpretation.

You can drop this file into:

```
.ampcode/04_PHASE_NOTES/Phase_7/HANDOVER.md
```

And you can paste it directly into a new chat with the dev.

---

# ⭐ **HANDOVER.md — Phase 7 CSS Modules Migration (Developer Onboarding)**

```md
# Phase 7 – Developer Handover  
**ForgeSyte Web‑UI CSS Modules Migration**

Welcome to Phase 7.  
This document contains everything you need to begin work immediately, with zero ambiguity and a fully stable Phase 6 baseline.

Phase 7 is a **pure styling migration**.  
No logic changes.  
No API changes.  
No test changes.  
No job‑pipeline changes.

This handover gives you:

1. The Phase 7 mission  
2. The guardrails (non‑negotiable)  
3. The component migration plan  
4. The PR workflow  
5. The verification steps  
6. The escalation process  
7. The reference documents  
8. The scripts (in Markdown)  
9. The success criteria  

Read this once, then begin Tier 1.

---

# 1. Phase 7 Mission

Migrate the entire web‑ui to **CSS Modules**, replacing all global/ad‑hoc styling with component‑scoped styles.

This is a **presentation‑only refactor**.

The job pipeline, API client, hooks, and Phase 6 logic **must remain untouched**.

---

# 2. Non‑Negotiable Guardrails

These files **must not change** during Phase 7:

- `web-ui/src/hooks/useVideoProcessor.ts`
- `web-ui/src/api/client.ts`
- `web-ui/src/api/pollJob.ts` and related helpers
- Any Phase 6 test files

Additionally:

- No new tests  
- No removed tests  
- No skipped tests (`it.skip`, `describe.skip`, `test.skip`, `xit`, etc.)  
- No server changes  
- No API changes  
- No job‑pipeline changes  
- No logic changes in components (CSS‑only)

If any of these must change, **stop immediately** and use the escalation template.

---

# 3. Component Migration Plan

Migration is done in **tiers**, smallest → largest:

### **Tier 1 — Leaf Components**
Simple, isolated components with minimal logic.

Examples:
- Button
- IconButton
- Tag / Badge
- Spinner
- Card
- Panel
- SectionTitle
- FormField / Input / Select

### **Tier 2 — Mid‑Level Layout Components**
Layout and navigation components.

Examples:
- Header
- Sidebar
- Navigation
- MainLayout / Shell
- Toolbar
- StatusBar
- Modal / Dialog

### **Tier 3 — Page‑Level Components**
Full pages and complex UI surfaces.

Examples:
- DashboardPage
- UploadPage
- ResultsPage
- SettingsPage
- JobsList

### **Tier 4 — Critical Components**
These are the most sensitive and must be done last.

Examples:
- VideoTracker
- VideoControls
- Timeline / Scrubber
- Overlays (players, ball, pitch, radar)
- Any component consuming job results

---

# 4. PR Workflow

Each PR must:

- Contain **only CSS Modules changes**
- Touch **only components in a single tier**
- Update `PHASE_7_COMPONENT_CHECKLIST.md`
- Pass all baseline checks
- Include the Phase 7 PR template

### Allowed JSX changes:
- Adding `className={styles.foo}`
- Importing the CSS module
- Removing old global class names

### Not allowed:
- New props
- New state
- New hooks
- New logic
- Changing component behaviour

---

# 5. Verification Steps (Run Before Every PR)

From repo root:

```
cd web-ui
npm test -- --run
npm run lint
npm run type-check
cd ..
uv run pre-commit run --all-files
```

All must pass.

---

# 6. Escalation Process

If you believe a logic change is required:

1. Stop immediately  
2. Open your PR  
3. Add a section titled:  
   **“Phase 7 Escalation – Logic Change Request”**  
4. Fill out the template in `PHASE_7_ESCALATION_TEMPLATE.md`  
5. Wait for approval before continuing  

No logic changes may be merged without explicit approval.

---

# 7. Reference Documents

All Phase 7 documents are located in:

```
.ampcode/04_PHASE_NOTES/Phase_7/
```

Key files:

- `PHASE_7_CSS_MODULES.md` — strategy & rules  
- `PHASE_7_COMPONENT_CHECKLIST.md` — migration tracking  
- `PHASE_7_ESCALATION_TEMPLATE.md` — logic change request  
- `01_NOTES.md` → `05_NOTES.md` — long‑form guidance  
- `PHASE_7_FORBIDDEN_FILE_CHECK.md` — guardrail script  
- `PHASE_7_SKIPPED_TESTS_CHECK.md` — skipped test detector  
- `PHASE_7_BASELINE_VERIFY.md` — baseline script  
- `PHASE_7_PR_GUARDRAIL.md` — combined PR guardrail  

---

# 8. Scripts (Markdown Only)

Scripts are stored as `.md` files for reference.  
You may copy/paste them locally if needed.

### Forbidden file check  
See: `PHASE_7_FORBIDDEN_FILE_CHECK.md`

### Skipped tests check  
See: `PHASE_7_SKIPPED_TESTS_CHECK.md`

### Baseline verification  
See: `PHASE_7_BASELINE_VERIFY.md`

### Combined PR guardrail  
See: `PHASE_7_PR_GUARDRAIL.md`

---

# 9. Success Criteria

Phase 7 is complete when:

- All components use CSS Modules  
- No global CSS remains (except reset/base)  
- No regressions in job pipeline  
- No regressions in upload/analyze flow  
- No regressions in results rendering  
- All tests pass (same count as Phase 6)  
- No skipped tests  
- No logic changes  
- CI green  
- Pre‑commit green  
- All tiers completed  
- All guardrails respected  

---

# 10. Start Here

Begin with:

**Tier 1 — Leaf Components**

Create a PR titled:

> Phase 7 – Tier 1 CSS Modules Migration (Leaf Components)

Follow the PR template and guardrails.

Once Tier 1 is merged, proceed to Tier 2.

---

# End of Handover

You now have everything needed to begin Phase 7 safely and efficiently.  
If anything is unclear, escalate before proceeding.

```

---

Roger — this is the **handover you needed**.  
It’s clean, authoritative, and ready to paste into a new chat with your dev.

If you want, I can also generate:

- A **Phase 7 Kickoff Message** to send to the dev  
- A **PR template file**  
- A **README for the Phase 7 folder**  
- A **developer checklist**  

Just say the word.