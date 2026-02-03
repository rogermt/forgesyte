# Phase 7 – CSS Modules Migration Plan

## Goal

Migrate the web‑ui from ad‑hoc/global styling to **CSS Modules**, without changing any runtime behaviour, API contracts, or test baselines established in Phase 6.

This is a **pure presentation refactor** under strict guardrails.

---

## Non‑Negotiable Guardrails

- No changes to:
  - `web-ui/src/hooks/useVideoProcessor.ts`
  - `web-ui/src/api/client.ts`
  - `web-ui/src/api/pollJob` (and related helpers)
  - Phase 6 test files
- No new tests added in Phase 7
- No skipped tests (`it.skip`, `describe.skip`, `test.skip`, `xit`, `xdescribe`, `xtest`)
- No changes to server code
- No changes to CI workflows
- No changes to job pipeline behaviour
- No changes to API routes or payloads

If any of the above must change, **stop and escalate** using `PHASE_7_ESCALATION_TEMPLATE.md`.

---

## Migration Strategy

1. **Tiered component migration**
   - Tier 1: Leaf components (buttons, badges, simple layout wrappers)
   - Tier 2: Mid‑level layout components (Header, Sidebar, Nav, Panels)
   - Tier 3: Page‑level components (Dashboard, Upload, Results, etc.)
   - Tier 4: Critical components (VideoTracker and anything touching job results)

2. **One PR per small, coherent scope**
   - Prefer 1–3 components per PR
   - Each PR must be reviewable by reading the diff without mental gymnastics

3. **Strict "CSS‑only" rule**
   - JSX/TSX changes limited to:
     - `className` wiring
     - Importing the CSS module
     - Removing old global class names
   - No new props, no new state, no new hooks, no new logic

4. **Baseline verification**
   - Before first Phase 7 PR:
     - `npm test -- --run`
     - `npm run lint`
     - `npm run type-check`
     - `uv run pre-commit run --all-files`
   - These commands must pass on the Phase 6 baseline and on every Phase 7 PR.

---

## CSS Modules Conventions

- File naming:
  - `ComponentName.module.css` next to `ComponentName.tsx`
- Import pattern:
  - `import styles from './ComponentName.module.css';`
- Usage:
  - `className={styles.root}`
  - `className={clsx(styles.root, styles.active)}`
- No global selectors:
  - No `body`, `html`, `*`, or global tag selectors
  - No `:global` unless explicitly justified and documented

---

## Component Migration Tiers

See `PHASE_7_COMPONENT_CHECKLIST.md` for the full component list and tier assignments.

High‑level:

- **Tier 1 (Leaf)**
  - Buttons, tags, badges, simple layout wrappers
- **Tier 2 (Mid‑level)**
  - Header, Sidebar, Navigation, Panels, Layout shells
- **Tier 3 (Page‑level)**
  - Dashboard, Upload page, Results page, Settings
- **Tier 4 (Critical)**
  - `VideoTracker` and any components tightly coupled to job results

---

## Success Criteria

- All targeted components use CSS Modules
- No regressions in:
  - Job pipeline behaviour
  - Upload/Analyze flow
  - Results rendering
- All tests passing (same count as Phase 6)
- No skipped tests
- CI green
- No changes to `useVideoProcessor`, `client.ts`, or job polling logic

If any of these cannot be met, escalate before merging.
