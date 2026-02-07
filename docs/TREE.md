# ForgeSyte Repository Structure

Complete directory tree of the ForgeSyte project.

```
forgesyte/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                           (Main CI/CD workflow)
│   │   └── execution-ci.yml                 (Execution governance CI)
│   ├── CODEOWNERS
│   └── pull_request_template.md
│
├── .ampcode/                                (Agent/development notes)
│   ├── 01_SPEC/
│   ├── 03_PLANS/                            (Phase-based planning docs)
│   │   ├── Phase_6/
│   │   ├── Phase_7/
│   │   ├── Phase_8/
│   │   ├── Phase_9/
│   │   ├── Phase_10/
│   │   ├── Phase_11/                        (Plugin registry/lifecycle)
│   │   └── Phase_12/                        (Execution governance)
│   ├── 04_PHASE_NOTES/                      (Detailed phase notes)
│   ├── 05_REFERENCES/
│   ├── 06_SUMMARIES/
│   ├── 07_PROJECT_RECOVERY/
│   ├── HANDOVER.md
│   ├── INDEX.md
│   └── README.md
│
├── server/                                  (Python/FastAPI backend)
│   ├── app/
│   │   ├── main.py                          (FastAPI app initialization)
│   │   ├── auth.py                          (Authentication middleware)
│   │   ├── models.py                        (Pydantic models)
│   │   ├── tasks.py                         (Background tasks)
│   │   ├── observability/                   (Device tracking, logging)
│   │   ├── core/
│   │   │   ├── errors/
│   │   │   │   └── error_envelope.py        (Error wrapping)
│   │   │   └── validation/
│   │   │       └── execution_validation.py  (Input/output validation)
│   │   ├── api_routes/
│   │   │   ├── routes/
│   │   │   │   ├── execution.py             (Execution API endpoints)
│   │   │   │   ├── plugins.py               (Plugin management API)
│   │   │   │   └── ...
│   │   │   └── __init__.py
│   │   ├── plugins/
│   │   │   ├── base.py                      (BasePlugin abstract class)
│   │   │   ├── inspector/                   (Plugin inspection service)
│   │   │   ├── loader/
│   │   │   │   └── plugin_registry.py       (Phase 11: Plugin registry)
│   │   │   ├── runtime/
│   │   │   │   ├── tool_runner.py           (Phase 11: ToolRunner)
│   │   │   │   └── sandbox.py               (Execution sandbox)
│   │   │   ├── health/                      (Plugin health checks)
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   ├── execution/                   (Phase 12: Execution services)
│   │   │   │   ├── analysis_execution_service.py    (API orchestration)
│   │   │   │   ├── job_execution_service.py         (Job lifecycle)
│   │   │   │   ├── plugin_execution_service.py      (ToolRunner delegation)
│   │   │   │   └── __init__.py
│   │   │   └── ...
│   │   ├── mcp/                             (MCP adapter)
│   │   ├── realtime/                        (WebSocket, job progress)
│   │   └── __init__.py
│   ├── tests/
│   │   ├── api/                             (REST API tests)
│   │   ├── api_typed_responses/             (Response validation tests)
│   │   ├── auth/                            (Authentication tests)
│   │   ├── contract/                        (JSON-safe output tests)
│   │   ├── execution/                       (Phase 12: Execution tests)
│   │   │   ├── test_analysis_execution_endpoint.py
│   │   │   ├── test_execution_integration.py
│   │   │   ├── test_job_execution_service.py
│   │   │   ├── test_plugin_execution_service.py
│   │   │   ├── test_registry_metrics.py
│   │   │   ├── test_toolrunner_validation.py
│   │   │   └── conftest.py
│   │   ├── helpers/                         (Test utilities)
│   │   ├── integration/                     (Full workflow tests)
│   │   ├── logging/                         (Logging tests)
│   │   ├── mcp/                             (MCP adapter tests)
│   │   ├── normalisation/
│   │   ├── observability/
│   │   ├── plugins/                         (Phase 11: Plugin tests)
│   │   │   ├── test_base_plugin.py
│   │   │   ├── test_entrypoint_loader.py
│   │   │   ├── test_plugin_metadata.py
│   │   │   ├── test_tool_runner_sandbox.py
│   │   │   └── ...
│   │   ├── realtime/
│   │   ├── services/
│   │   ├── tasks/
│   │   ├── unit/
│   │   ├── websocket/
│   │   ├── test_plugin_health_api/
│   │   └── conftest.py
│   ├── pyproject.toml                       (Python dependencies, pytest config)
│   ├── uv.lock                              (Locked dependencies)
│   └── README.md
│
├── web-ui/                                  (React/TypeScript frontend)
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/                             (API client)
│   │   ├── hooks/
│   │   ├── styles/
│   │   ├── types/
│   │   ├── utils/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── tests/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── vitest.config.ts
│   └── README.md
│
├── scripts/
│   ├── scan_execution_violations.py         (Phase 12: Mechanical scanner)
│   └── ...
│
├── docs/
│   ├── design/
│   │   ├── execution-governance.md          (Execution governance docs)
│   │   ├── execution-architecture.drawio    (Draw.io diagram)
│   │   ├── execution-onboarding.md          (Developer onboarding)
│   │   ├── video-tool-runner.md
│   │   └── ...
│   ├── issues/
│   │   ├── ISSUES_LIST.md
│   │   └── ...
│   ├── phase12-wrap-up.md                   (Phase 12 summary)
│   ├── repo-audit-checklist.md              (Governance audit)
│   ├── execution-onboarding.md
│   ├── TREE.md                              (This file)
│   └── ...
│
├── fixtures/                                (Test fixtures)
│   └── README.md
│
├── scratch/                                 (Temporary/scratch files)
│
├── .pre-commit-config.yaml                  (Pre-commit hooks)
├── .gitignore
├── AGENTS.md                                (Agent conventions & commands)
├── ARCHITECTURE.md
├── BRANDING.md
├── CONTRIBUTING.md
├── GEMINI.md
├── PLUGIN_DEVELOPMENT.md
├── QWEN.md
├── README.md                                (Main readme)
├── ROADMAP.md
├── e2e.test.sh                              (E2E test script)
├── forgesyte.code-workspace
├── gemini-extension.json
└── requirements-lint.txt
```

---

## Key Directories by Function

| Directory | Purpose |
|-----------|---------|
| `server/app/` | FastAPI application code |
| `server/app/plugins/` | Plugin system (Phase 11) |
| `server/app/services/execution/` | Execution layer (Phase 12) |
| `server/tests/` | All test suites |
| `server/tests/execution/` | Execution governance tests (Phase 12) |
| `server/tests/plugins/` | Plugin registry/ToolRunner tests (Phase 11) |
| `web-ui/src/` | React/TypeScript frontend |
| `scripts/` | Utility scripts (scanner, etc.) |
| `docs/design/` | Architecture & design documentation |
| `.ampcode/` | Development notes & planning (not deployed) |
| `.github/workflows/` | CI/CD pipelines |

---

## Test Organization

```
server/tests/
├── api/                      (REST API endpoints)
├── execution/                (Job execution, ToolRunner) — Phase 12
├── plugins/                  (Plugin registry, loader) — Phase 11
├── mcp/                      (MCP adapter)
├── realtime/                 (WebSocket, job progress)
├── contract/                 (JSON-safe output validation)
├── integration/              (Full workflow tests)
├── services/                 (Service layer)
├── tasks/                    (Background jobs)
├── auth/                     (Authentication)
└── ...
```

---

## Configuration Files

| File | Purpose |
|------|---------|
| `server/pyproject.toml` | Python deps, pytest, mypy, ruff |
| `web-ui/package.json` | Node deps, npm scripts |
| `.pre-commit-config.yaml` | Git pre-commit hooks |
| `.github/workflows/*.yml` | CI/CD pipelines |
| `.gitignore` | Git ignore rules |
| `tsconfig.json` | TypeScript config |
| `vite.config.ts` | Vite bundler config |

---

## Documentation

| File | Purpose |
|------|---------|
| `README.md` | Main project overview |
| `AGENTS.md` | Agent conventions & commands |
| `ARCHITECTURE.md` | System architecture |
| `docs/design/execution-governance.md` | Execution governance docs |
| `docs/phase12-wrap-up.md` | Phase 12 summary |
| `docs/repo-audit-checklist.md` | Audit checklist |
| `PLUGIN_DEVELOPMENT.md` | Plugin development guide |
| `CONTRIBUTING.md` | Contribution guidelines |

---

## Important Notes

- **No phase-named folders**: All code organized by functionality, not phase
- **Developers think in features**: API, plugins, execution, MCP, realtime, etc.
- **Phases are implementation details**: Not part of public API or structure
- **Tests follow structure**: `tests/execution/`, `tests/plugins/`, etc.
- **CI enforces governance**: Mechanical scanner + test suite on every push
