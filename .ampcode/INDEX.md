# ForgeSyte – .ampcode Index (Phase 10 Complete, Phase 11 Specification Ready)

**Note:** This directory contains **governance documentation only** — no executable code or scripts.
All implementation code lives in `/server` and `/web-ui`.

## 01_SPEC
- PHASE_5_8_SPEC_LOCKED.md
- COMPLETE_CODE_SPEC.md
- ARCHITECTURE_BEFORE_AFTER.md

## 02_DECISIONS
- APPROVED_DECISIONS.md
- LOCKED_DECISIONS_FINAL.md
- GUARDRAILS_LOCKED.md

## 03_PLANS
- MIGRATION_PLAN.md
- COMMIT_PLAN.md
- MASTER_CHECKLIST_LOCKED.md
- Phase_8/
  - PHASE_8_PLANS.md
  - PHASE_8_CONTEXT_CHECKPOINT.md
- Phase_10/ ✅ COMPLETE
  - PHASE_10_PLANS.md
- Phase_11/ 🚀 SPECIFICATION READY
  - PHASE_11_PLANS.md
  - PHASE_11_PROGRESS.md

## 04_PHASE_NOTES
- Phase_6A.md
- Phase_6B.md
- Phase_7/ ✅ COMPLETE
  - 01_NOTES.md
  - 02_NOTES.md
  - 03_NOTES.md
  - 04_NOTES.md
  - 05_NOTES.md
  - 06_NOTES.md
  - PHASE_7_COMPONENT_CHECKLIST.md
  - PHASE_7_CSS_MODULES.md
  - PHASE_7_ESCALATION_TEMPLATE.md
  - PHASE_7_BASELINE_VERIFY.md
  - PHASE_7_PR_CHECKLIST.md
  - PHASE_7_GUARDRAILS_SCRIPT.md
  - PHASE_7_SKIPPED_TESTS_CHECK.md
  - TIER_1_ACCEPTANCE_VERIFICATION.md
  - TIER_2_ANALYSIS.md ✅ (Tier 2-4 N/A)
- Phase_8/ ✅ COMPLETE
   - PHASE_8_README.md
   - PHASE_8_KICKOFF.md
   - PHASE_8_NOTES_01.md
   - PHASE_8_NOTES_02.md (DuckDB + structured logging deep dive)
   - PHASE_8_NOTES_03.md
   - PHASE_8_NOTES_04.md (Steps 4-6 TDD overview)
   - PHASE_8_METRICS_SCHEMA.sql (governance spec — canonical schema definition)
   - PHASE_8_NORMALISATION_SCHEMA.md (canonical output schema)
   - PHASE_8_STEP_4_TDD.md (Overlay Renderer — Web UI)
   - PHASE_8_STEP_5_TDD.md (FPS Throttling + Performance)
   - PHASE_8_STEP_6_TDD.md (Device Selector)
   - PHASE_8_ACCEPTANCE_CHECKLIST.md
   - PHASE_8_ESCALATION_TEMPLATE.md
   - PHASE_8_TO_PHASE_9.md (transition plan)
- Phase_9/ ✅ COMPLETE
   - PHASE_9_COMPLETE.md
- Phase_10/ ✅ COMPLETE
   - PHASE_10_KICKOFF.md
   - PHASE_10_DEVELOPER_CONTRACT.md
   - PHASE_10_API_SPEC.md
   - PHASE_10_UI_SPEC.md
   - PHASE_10_RED_TESTS.md
   - PHASE_10_GREEN_TESTS.md (implied)
- Phase_11/ 🚀 SPECIFICATION COMPLETE → IMPLEMENTATION PENDING
   - PHASE_11_KICKOFF.md
   - PHASE_11_ARCHITECTURE.md
   - PHASE_11_RED_TESTS.md
   - PHASE_11_CONCRETE_IMPLEMENTATION.md
   - PHASE_11_PLUGIN_LOADER_V2.md
   - PHASE_11_VIDEOTRACKER_STABILITY.md
   - PHASE_11_GREEN_TESTS.md
   - PHASE_11_DEVELOPER_CONTRACT.md
   - PHASE_11_IMPLEMENTATION_PLAN.md
   - PHASE_11_PR_TEMPLATE.md
   - PHASE_11_COMPLETION_CRITERIA.md
   - PHASE_11_FOLDER_SCAFFOLDING.md
- Phase_12/ 📋 KICKOFF DOCUMENTED
   - PHASE_12_KICKOFF.md (Multi-plugin orchestration vision)

## 05_REFERENCES
- REACT_REFERENCES_NEEDED.md
- COMPLETE_REACT_REFERENCES_LIST.md
- REACTJS_DEV_LLMS.txt
- react/*.md

## 06_SUMMARIES
- DELIVERY_SUMMARY.txt
- QUICK_REFERENCE.txt

## 07_PROJECT_RECOVERY
- WEB-UI_ISSUE_146.md
- HANDOVER.md

---

## Purpose

This directory is the **single source of truth** for all ForgeSyte engineering governance.

Every file is intentional, canonical, and version-controlled.

**Phase Status:**
- ✅ Phase 6: Complete (Web-UI stabilized, job pipeline fixed)
- ✅ Phase 7: Complete (CSS Modules migrated Tier 1, Tiers 2-4 N/A)
- ✅ Phase 8: Complete (DuckDB, structured logging, metrics, normalization)
- ✅ Phase 9: Complete (UI controls, device selector, FPS slider)
- ✅ Phase 10: Complete (Real-time WebSocket, progress tracking, plugin inspector)
- 🚀 Phase 11: Specification Complete → Implementation Pending
  - ✅ Architecture documented (12 docs, 5,784 lines)
  - ✅ RED tests defined (40+ test cases)
  - ✅ Completion criteria locked (7 objective items)
  - 📋 Implementation ready to begin (8 commits, 4 weeks)
  - 📋 Governance tools ready (audit_plugins.py, PR template)
- 📋 Phase 12: Kickoff documented (Multi-plugin orchestration)