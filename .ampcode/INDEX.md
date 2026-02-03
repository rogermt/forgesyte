# ForgeSyte – .ampcode Index (Phase 7 Complete, Phase 8 In Progress)

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
- Phase_8/ 🚀 IN PROGRESS
  - PHASE_8_README.md
  - PHASE_8_KICKOFF.md
  - PHASE_8_NOTES_01.md
  - PHASE_8_NOTES_02.md (DuckDB + structured logging deep dive)
  - PHASE_8_NOTES_03.md
  - PHASE_8_METRICS_SCHEMA.sql (governance spec — canonical schema definition)
  - PHASE_8_ACCEPTANCE_CHECKLIST.md
  - PHASE_8_ESCALATION_TEMPLATE.md
  - PHASE_8_TO_PHASE_9.md (transition plan)

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
- 🚀 Phase 8: In progress
  - ✅ Step 1: DuckDB schema foundation + load_schema.py + schema drift CI guardrail
  - ✅ Step 2: Structured logging unit tests (context.py, filters.py, capture.py)
  - 📝 Step 2 (cont.): Integration tests + job pipeline wiring
  - 📋 Steps 3-6: Normalisation, overlay renderer, FPS controls, device selector, governance