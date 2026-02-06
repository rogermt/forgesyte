# Phase 12 — Folder Scaffolding

This document defines the required folder and file structure for Phase 12.
Only governance files belong in .ampcode. All coding files belong in the
project's real source tree.

---

# 1. Governance Files (This Folder)

All Phase 12 governance files MUST live here:

/home/rogermt/forgesyte/.ampcode/04_PHASE_NOTES/Phase_12/

Required files:
- PHASE_12_KICKOFF.md
- PHASE_12_INVARIANTS.md
- PHASE_12_PR_TEMPLATE.md
- PHASE_12_MIGRATION_CHECKLIST.md
- PHASE_12_EXECUTION_PATH_DIAGRAM.md
- PHASE_12_TOOLRUNNER_LIFECYCLE.md
- PHASE_12_PLUGIN_EXECUTION_FLOW.md
- PHASE_12_DEVELOPER_CONTRACT.md
- PHASE_12_CONCRETE_IMPLEMENTATION.md
- PHASE_12_COMPLETION_CRITERIA.md
- PHASE_12_ARCHITECTURE.md
- PHASE_12_FOLDER_SCAFFOLDING.md
- PHASE_12_API_CONTRACT.md

No coding files may appear here.

---

# 2. Backend Coding Files (Real Project Structure)

server/app/plugins/runtime/
    tool_runner.py        (Phase 12 core implementation)

server/app/plugins/loader/
    plugin_registry.py    (registry updates)

server/app/services/
    analysis_service.py
    job_management_service.py
    plugin_management_service.py

server/tests/phase_12/
    test_execution_path_fails_initially.py
    test_toolrunner_called_for_all_plugins.py
    test_no_direct_plugin_run_calls.py
    test_registry_metrics_not_updated_yet.py
    test_unstructured_errors_fail.py
    test_invalid_plugin_output_fails.py
    test_input_validation_fails.py

---

# 3. No Other Folders Added

Phase 12 does NOT introduce:
- new plugin folders
- new API folders
- new UI folders

Only ToolRunner and registry integration change.
