# Repository Audit Checklist

Use this checklist to verify the repository is consistent, governed, and free of drift.

---

## A. Directory Structure

- [ ] No phase‑named folders
- [ ] Execution code lives in functional directories
- [ ] Tests live under `server/tests/execution/`
- [ ] Documentation lives under `docs/`

---

## B. Execution Architecture

- [ ] ToolRunner is the only caller of plugin.run()
- [ ] PluginExecutionService delegates correctly
- [ ] JobExecutionService manages lifecycle correctly
- [ ] AnalysisExecutionService exposes sync + async paths
- [ ] API routes match service methods

---

## C. Lifecycle States

- [ ] Only LOADED, INITIALIZED, RUNNING, FAILED, UNAVAILABLE
- [ ] No SUCCESS/ERROR lifecycle states
- [ ] Registry updates state correctly

---

## D. Validation + Error Envelope

- [ ] Input validation always runs
- [ ] Output validation always runs
- [ ] Error envelope always wraps exceptions
- [ ] API never returns raw exceptions

---

## E. Scanner

- [ ] Scanner exists
- [ ] Scanner enforces all invariants
- [ ] Scanner passes locally
- [ ] Scanner blocks regressions

---

## F. CI Pipeline

- [ ] CI workflow exists
- [ ] Scanner runs first
- [ ] Phase 11 tests run
- [ ] Execution tests run
- [ ] CI fails on violations

---

## G. Documentation

- [ ] Execution governance doc exists
- [ ] Architecture diagrams exist
- [ ] Onboarding guide exists
- [ ] README updated

---

## H. Developer Experience

- [ ] Running tests is easy
- [ ] Running scanner is easy
- [ ] Adding plugins is documented
- [ ] Adding execution features is documented

---

This checklist should be run before major releases or structural changes.
