# Phase 7 – Component Migration Checklist (CSS Modules)

This file tracks **which components have been migrated** to CSS Modules and in which tier they belong.

## Legend

- [ ] Not started
- [~] In progress (PR open)
- [x] Completed and merged

---

## Tier 1 – Leaf Components

**Status:** ✅ COMPLETE — Only 2 components in codebase use className (both migrated)

- [x] RecordButton (migrated Feb 3, 2026)
- [x] OverlayToggles (migrated Feb 3, 2026)

**Note:** Other theoretical leaf components (Button, IconButton, Badge, etc.) do not exist in current codebase. Only RecordButton and OverlayToggles use CSS classNames.

---

## Tier 2 – Mid-Level Layout Components

**Status:** Awaiting Tier 1 approval before starting

Actual components in codebase:
- [ ] PluginSelector
- [ ] ToolSelector
- [ ] CameraPreview
- [ ] ConfidenceSlider
- [ ] ConfigPanel

---

## Tier 3 – Major Layout Components

**Status:** Awaiting Tier 1-2 approval

Actual components in codebase:
- [ ] ResultsPanel
- [ ] JobList
- [ ] ResultOverlay

---

## Tier 4 – Critical Video/Rendering Components

**Status:** Awaiting Tier 1-3 approval (highest risk tier)

Actual components in codebase:
- [ ] VideoTracker (complex, video stream integration)
- [ ] BoundingBoxOverlay (canvas-based rendering)
- [ ] RadarView (canvas-based rendering)

---

## Rules Per PR

- [ ] Only components from a **single tier** in each PR
- [ ] No changes to hooks, API client, or job logic
- [ ] No new tests, no removed tests
- [ ] No skipped tests
- [ ] `npm test -- --run` passes
- [ ] `npm run lint` passes
- [ ] `npm run type-check` passes
- [ ] `uv run pre-commit run --all-files` passes

---

## Notes

- If a component spans multiple concerns (layout + logic), **only** the styling aspects should change in Phase 7.
- If a migration requires logic changes, stop and use `PHASE_7_ESCALATION_TEMPLATE.md`.
