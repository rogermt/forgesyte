# Phase 7 – Component Migration Checklist (CSS Modules)

This file tracks **which components have been migrated** to CSS Modules and in which tier they belong.

## Legend

- [ ] Not started
- [~] In progress (PR open)
- [x] Completed and merged

---

## Tier 1 – Leaf Components

- [ ] Button
- [ ] IconButton
- [ ] Tag / Badge
- [ ] Spinner / Loader
- [ ] Card
- [ ] Panel
- [ ] SectionTitle
- [ ] FormField / Input / Select

---

## Tier 2 – Mid‑Level Layout Components

- [ ] Header
- [ ] Sidebar
- [ ] Navigation / NavLinks
- [ ] MainLayout / Shell
- [ ] Toolbar
- [ ] StatusBar / Footer
- [ ] Modal / Dialog

---

## Tier 3 – Page‑Level Components

- [ ] DashboardPage
- [ ] UploadPage
- [ ] ResultsPage
- [ ] SettingsPage
- [ ] JobsList / HistoryView

---

## Tier 4 – Critical Components

- [ ] VideoTracker
- [ ] VideoControls
- [ ] Timeline / Scrubber
- [ ] Overlays (players, ball, pitch, radar)
- [ ] Any component directly consuming job results

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
