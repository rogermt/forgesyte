# Agent Commands and Conventions for ForgeSyte

This document defines essential commands and conventions for agents working on the ForgeSyte project.

## Project Overview

ForgeSyte is a modular AI-vision MCP server engineered for developers, featuring:
- **Server (Python/FastAPI)**: `/server` - Backend API, plugin management, job processing
- **Web-UI (React/TypeScript)**: `/web-ui` - Frontend client application
- **Plugin Architecture**: Modular vision analysis plugins (OCR, YOLO tracker, etc.)
- **Job-Based Pipeline**: Async job processing with `/v1/analyze` endpoint
- **MCP Integration**: Model Context Protocol for tool exposure
- **WebSocket Streaming**: Real-time video processing via `/v1/stream` and `/ws/video/stream`

**Current Phase**: Phase 17 - Real-Time Streaming Inference (4/12 backend commits completed)

---

## Python Server (Backend)

All commands run from the `server/` directory.

### Setup and Dependencies

```bash
cd server

# Sync dependencies with uv
uv sync

# Install pre-commit hooks
uv pip install pre-commit
uv run pre-commit install
```

### Testing

```bash
# Run all tests with coverage
uv run pytest --cov=app --cov-report=term-missing

# Run a single test file
uv run pytest tests/api/test_jobs.py -v

# Run a single test class
uv run pytest tests/api/test_jobs.py::TestJobsEndpoint -v

# Run a single test method
uv run pytest tests/api/test_jobs.py::TestJobsEndpoint::test_list_jobs -v

# Run tests matching a pattern
uv run pytest -k "test_list" -v

# Run tests with a specific marker
uv run pytest -m asyncio -v

# Run contract tests (JSON-safe output validation)
# Run execution governance tests
uv run pytest tests/execution -v

# Run plugin registry tests
uv run pytest tests/plugins -v

# Run Phase 17 streaming tests (NEW)
uv run pytest tests/streaming/ -v

# Run specific Phase 17 test files
uv run pytest tests/streaming/test_connect.py -v
uv run pytest tests/streaming/test_session_manager.py -v
uv run pytest tests/streaming/test_frame_validator.py -v
```

### Linting and Formatting

```bash
# Format code with Black
uv run black app/ tests/

# Lint with Ruff (auto-fix)
uv run ruff check --fix app/ tests/

# Type checking with Mypy
uv run mypy app/ --no-site-packages

# Run all quality checks
uv run black app/ tests/ && uv run ruff check --fix app/ tests/ && uv run mypy app/ --no-site-packages

# Full pre-commit check
uv run pre-commit run --all-files
```

### Execution Governance Verification

Before committing ANY changes, verify the CI workflow would pass locally.

**Run all of these in order:**

```bash
# 1. Run execution governance scanner (repo root)
python scripts/scan_execution_violations.py

# 2. Run plugin registry tests
cd server && uv run pytest tests/plugins -v

# 3. Run execution governance tests
cd server && uv run pytest tests/execution -v

# 4. Run all core tests (full suite - matches CI)
cd server && uv run pytest tests/ -v --tb=short
```

**All four MUST PASS before committing.**

These are the exact same checks that `.github/workflows/execution-ci.yml` runs on every PR and push to `main`.
If any step fails locally, it will also fail in CI — do not commit until all pass.

### Server Structure

```
server/
├── app/
│   ├── api_routes/       # API route handlers
│   │   └── routes/
│   │       ├── video_stream.py          # NEW: Phase 17 WebSocket streaming endpoint
│   │       ├── video_file_processing.py
│   │       ├── video_submit.py
│   │       ├── job_status.py
│   │       ├── job_results.py
│   │       └── execution.py
│   ├── core/             # Core application logic
│   ├── examples/         # Example usage code
│   ├── logging/          # Logging configuration
│   ├── mcp/              # MCP (Model Context Protocol) implementation
│   ├── observability/    # Observability features
│   ├── plugins/          # Plugin system core
│   ├── realtime/         # Real-time processing
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic services
│   │   ├── streaming/    # NEW: Phase 17 streaming services
│   │   │   ├── session_manager.py  # Per-connection state management
│   │   │   ├── frame_validator.py   # JPEG frame validation
│   │   │   └── backpressure.py      # Backpressure decision logic
│   │   ├── dag_pipeline_service.py   # DAG pipeline execution (updated with is_valid_pipeline)
│   │   ├── video_file_pipeline_service.py  # Video file processing (updated with is_valid_pipeline)
│   │   └── ...
│   ├── main.py           # FastAPI application entry point
│   ├── models.py         # Database models
│   ├── routes_pipeline.py # Pipeline REST endpoints
│   └── websocket_manager.py # WebSocket handling
└── tests/
    ├── api/              # API endpoint tests
    ├── contract/         # Contract validation tests
    ├── execution/        # Execution governance tests
    ├── streaming/        # NEW: Phase 17 streaming tests
    │   ├── test_connect.py           # WebSocket connection tests
    │   ├── test_session_manager.py   # Session manager tests
    │   └── test_frame_validator.py   # Frame validator tests
    ├── plugins/          # Plugin tests
    └── websocket/        # Legacy WebSocket tests
```

### Code Style (Python)

- **Formatting**: Follow PEP 8, use Black (line-length 88)
- **Imports**: Sort with Ruff/isort, group: stdlib, third-party, local
- **Types**: Use type hints; `Decimal` for money/precision
- **Naming**: `snake_case` functions/variables, `PascalCase` classes
- **Paths**: Use `pathlib` instead of `os.path`
- **Error Handling**: Catch specific exceptions, use custom error types
- **Async**: Use `async def` for I/O, don't mix sync/async
- **Logging**: Use `logging` module, not `print()`
- **Docstrings**: Write for all public classes/functions
- **Registry Pattern**: Use decorators for plugin/command registration
- **Streaming Services (Phase 17)**:
  - Use `SessionManager` for per-connection state (ephemeral, no persistence)
  - Use `FrameValidationError` for structured frame validation errors
  - Use `Backpressure` class for backpressure decision logic
  - Log all streaming events with structured JSON format
  - Follow TDD: Write tests first, implement code to make tests pass

---

## React Web-UI (Frontend Client)

All commands run from the `web-ui/` directory.

### Setup and Dependencies

```bash
cd web-ui

# Install dependencies
npm install
```

### Testing

```bash
# Run all tests (vitest with watch mode)
npm run test

# Run tests once (no watch mode)
npm run test -- --run

# Run a single test file
npm run test -- src/api/client.test.ts

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage

# Type check (MANDATORY - see below)
npm run type-check

# Lint
npm run lint

# Run both lint AND type-check (matches CI workflow)
cd web-ui && npm run lint && npm run type-check
# or simply:
npm run check

# Build for production
npm run build

# Run integration tests (requires running server)
npm run test:integration

# Run dev server
npm run dev

# Preview production build
npm run preview
```

**CRITICAL:** `npm run type-check` is MANDATORY for ALL web-ui changes.
Vitest does NOT enforce TypeScript strict type checking — tests can pass
even when `tsc --noEmit` fails. CI runs `tsc --noEmit` and WILL reject
commits that skip this step. NEVER commit web-ui changes without running
`npm run type-check` first.

### Web-UI Structure

```
web-ui/
├── src/
│   ├── api/              # API client and types
│   ├── components/       # React components
│   ├── hooks/            # Custom React hooks
│   ├── integration/      # Integration tests
│   ├── realtime/         # Real-time (WebSocket) logic
│   ├── stories/          # Storybook stories
│   ├── test/             # Test utilities and setup
│   ├── tests/            # Test files
│   ├── types/            # TypeScript type definitions
│   ├── utils/            # Utility functions
│   ├── App.tsx           # Main application component
│   └── main.tsx          # Application entry point
└── tests/                # Additional test files
```

### Code Style (TypeScript/React)

- **Types**: Define interfaces for all props, state, and API responses
- **No `any`**: Use proper types or `unknown`
- **Imports**: Group: React, external libs, local modules
- **Files**: PascalCase for components (`ImagePreview.tsx`), camelCase for utilities
- **Hooks**: Prefix custom hooks with `use`
- **Components**: Functional components with hooks, no class components
- **State**: Keep local unless globally needed
- **Effects**: Always cleanup in `useEffect` return

---

## WebSocket Streaming

The project supports two WebSocket endpoints for real-time video processing:

### 1. Legacy WebSocket Endpoint (`/v1/stream`)
- **Purpose**: Plugin-based real-time analysis
- **Protocol**: WebSocket with JSON messages
- **Usage**: Motion detection, object detection
- **Tests**: `server/tests/websocket/`

### 2. Phase 17 Streaming Endpoint (`/ws/video/stream`) - NEW
- **Purpose**: Real-time frame-by-frame inference through Phase 15 pipelines
- **Protocol**: WebSocket with binary frame input, JSON result output
- **Features**:
  - Accepts binary JPEG frames
  - Validates frames (SOI/EOI markers, size limits)
  - Runs Phase 15 DAG pipelines per frame
  - Implements backpressure (drop frames / slow-down signals)
  - Ephemeral sessions (no persistence)
- **Connection**: `ws://<host>/ws/video/stream?pipeline_id=<id>`
- **Tests**: `server/tests/streaming/` (24/24 tests passing)
- **Status**: Phase 17 - 4/12 backend commits completed

### WebSocket Message Protocol (Phase 17)

**Incoming Messages**:
- Type: Binary
- Format: JPEG bytes
- Constraints: Max 5MB, must contain JPEG SOI/EOI markers

**Outgoing Messages**:
- Success: `{"frame_index": N, "result": {...}}`
- Dropped: `{"frame_index": N, "dropped": true}`
- Slow-down: `{"warning": "slow_down"}`
- Error: `{"error": "<code>", "detail": "<message>"}`

**Error Codes**:
- `invalid_message` - Expected binary frame payload
- `invalid_frame` - Not a valid JPEG image
- `frame_too_large` - Frame exceeds 5MB
- `invalid_pipeline` - Unknown pipeline_id
- `pipeline_failure` - Pipeline execution failed
- `internal_error` - Unexpected error occurred

---

## End-to-End Tests

```bash
# Run full E2E test suite (starts server + runs web-ui integration tests)
./e2e.test.sh
```

---

## CI/CD Workflows

The project uses two GitHub Actions workflows:

### 1. CI Workflow (`.github/workflows/ci.yml`)

Runs on every push and pull request to `main` or `develop`:

- **Lint Job**: Runs pre-commit hooks (black, ruff, mypy, eslint)
- **Server Tests Job**: Runs pytest with coverage on Python 3.8-3.11
- **Web-UI Job**: Runs eslint, type-check, and vitest
- **E2E Job**: Runs full end-to-end tests
- **Test Integrity Job**: Enforces test coverage doesn't decrease (PR only)
- **Skipped Test Policy Job**: Validates skipped tests have APPROVED comments (PR only)
- **Server Health Job**: Runtime validation of plugins, analyze, jobs, websocket

### 2. Execution Governance CI (`.github/workflows/execution-ci.yml`)

Runs on every PR and push to `main`:

- Execution governance scanner
- Plugin registry tests
- Execution governance tests
- All core tests

---

## GPU/CPU Setup Note

- **Server + GPU plugins**: Run on Kaggle (server and plugins cloned there)
- **Web-UI + CPU-only plugins**: Run locally on CPU laptop (where I can edit)
- **Connection**: Uses local tunnel so web-ui can connect to server on Kaggle

This means:
- I do NOT have access to GPU plugin code - you will copy/paste GPU code to me
- I CAN edit CPU-only plugins and all other code
- CPU-only plugins: All processing uses CPU
- GPU plugins: Processing uses GPU on Kaggle
- When you paste GPU code, I can help with CPU-related issues, testing, or integration, but not GPU-specific debugging

---

## Key Configuration Files

| File | Purpose |
|------|---------|
| `server/pyproject.toml` | Python dependencies, pytest, mypy, ruff config |
| `web-ui/package.json` | Node dependencies, npm scripts, vitest config |
| `.pre-commit-config.yaml` | Pre-commit hooks (black, ruff, mypy, eslint) |
| `web-ui/tsconfig.json` | TypeScript strict mode config |
| `web-ui/vitest.config.ts` | Vitest test configuration |
| `web-ui/.eslintrc.cjs` | ESLint configuration |
| `e2e.test.sh` | Full E2E test script |

### Environment Variables (Phase 17 Streaming)

| Variable | Default | Description |
|----------|---------|-------------|
| `STREAM_DROP_THRESHOLD` | `0.10` | Drop frames when drop rate exceeds 10% |
| `STREAM_SLOWDOWN_THRESHOLD` | `0.30` | Send slow-down warning when drop rate exceeds 30% |
| `STREAM_MAX_FRAME_SIZE_MB` | `5` | Maximum frame size in megabytes |
| `STREAM_MAX_SESSIONS` | `10` | Recommended maximum concurrent sessions (not enforced) |

---

## Git Workflow

### Creating a Feature Branch

```bash
# Create and switch to a new feature branch
git checkout -b feature/description
```

### TDD Workflow (Required)

For any feature or bug fix, follow Test-Driven Development:

1. **Write failing tests first** - Define expected behavior
2. **Run tests to verify they fail** - Confirm tests catch the issue
3. **Implement code** - Write minimal code to make tests pass
4. **Run tests to verify they pass** - Confirm implementation works
5. **Run lint, type check, and execution governance verification** - Ensure code quality
6. **Save test logs** - Save test output to log file as proof of GREEN status
7. **Commit** - Only commit when ALL tests pass and test logs are saved

**Before committing, run the full verification suite:**

```bash
# For Python/Server changes:
uv run pre-commit run --all-files          # black/ruff/mypy
cd server && uv run pytest tests/ -v       # all tests
python scripts/scan_execution_violations.py # governance check

# For TypeScript/Web-UI changes (ALL THREE are required):
cd web-ui
npm run lint                               # eslint
npm run type-check                         # tsc --noEmit (MANDATORY)
npm run test -- --run                      # vitest
```

**Phase 17 Test Logs**:
All Phase 17 backend commit test logs are saved to `/tmp/`:
```
/tmp/phase17_backend_commit_01_initial.log    # GREEN verification before Commit 1
/tmp/phase17_backend_commit_01_test_red.log   # RED verification for Commit 1
/tmp/phase17_backend_commit_01_final.log      # GREEN verification after Commit 1
/tmp/phase17_backend_commit_02_initial.log    # GREEN verification before Commit 2
/tmp/phase17_backend_commit_02_test_red.log   # RED verification for Commit 2
/tmp/phase17_backend_commit_02_final.log      # GREEN verification after Commit 2
/tmp/phase17_backend_commit_03_final.log      # GREEN verification after Commit 3
/tmp/phase17_backend_commit_04_final.log      # GREEN verification after Commit 4
```

View test results:
```bash
# View final test results for Commit 1
cat /tmp/phase17_backend_commit_01_final.log | tail -20

# Count passed tests
grep "passed" /tmp/phase17_backend_commit_01_final.log
```

### Phase 17 TDD Workflow (Backend)

For Phase 17 streaming features, follow strict TDD:

1. **Verify GREEN**: Run full test suite - all tests must pass BEFORE starting
2. **Write FAILING test**: Write test for new functionality
3. **Verify RED**: Run test - it MUST fail
4. **Implement code**: Write minimal code to make test pass
5. **Verify GREEN**: Run full test suite - ALL tests must pass
6. **Save test logs**: Save test output to `/tmp/phase17_backend_commit_<N>.log`
7. **Commit**: Only commit when ALL tests pass and test logs are saved

**Example Phase 17 TDD workflow**:
```bash
cd server

# 1. Verify GREEN before starting
uv run pytest tests/ -v --tb=short > /tmp/phase17_backend_commit_01_initial.log

# 2. Write failing test
# 3. Verify RED
uv run pytest tests/streaming/test_connect.py -v

# 4. Implement code

# 5. Verify GREEN
uv run pytest tests/ -v --tb=short > /tmp/phase17_backend_commit_01_final.log

# 6. Save test log (already done above)

# 7. Commit
git add .
git commit -m "feat(backend): Commit 1 - WebSocket Router + Endpoint Skeleton

Tests passed: 1211 passed, 10 warnings
Test log: /tmp/phase17_backend_commit_01_final.log"
```

**Critical**: Never commit when any test is failing. All test logs must be saved as proof of GREEN status.

```bash
# Example TDD workflow
cd web-ui

# 1. Write failing test
# 2. Run specific test to verify it fails
npm run test -- --run src/App.tdd.test.tsx

# 3. Implement code to fix the test

# 4. Run test to verify it passes
npm run test -- --run src/App.tdd.test.tsx

# 5. Run lint and type check
npm run lint
npm run type-check

# 6. Commit
git add .
git commit -m "fix: description of what was fixed"
```

### Committing and PR

```bash
# Stage and commit changes
git add .
git commit -m "type: description"

# Push feature branch
git push origin feature/description

# Create PR using gh CLI
gh pr create --base main --head feature/description --title "type: description"

# After PR is reviewed and approved, merge locally and push
git checkout main
git pull origin main
git merge feature/description
git push origin main
```

### Current Branch Status

**Active Branch**: `feature/phase-17`

**Recent Commits**:
```
e1194c6 feat(backend): Commit 4 - Integrate SessionManager into WebSocket
73eac73 feat(backend): Commit 3 - Frame Validator
94f1a7e feat(backend): Commit 2 - Session Manager Class
3e103a5 feat(backend): Commit 1 - WebSocket Router + Endpoint Skeleton
4620506 docs: Phase 17 documentation complete
```

**Test Status**: All streaming tests passing (24/24)

### Pre-Commit Hook Safety (IMPORTANT)

**NEVER use `--no-verify` to bypass hooks.**

Pre-commit hooks enforce quality standards:

- **black**: Code formatting
- **ruff**: Linting
- **mypy**: Type checking
- **eslint**: JavaScript/TypeScript linting
- **server-tests**: Runs pytest before commit
- **validate-skipped-tests**: Ensures skipped tests have APPROVED comments
- **prevent-test-changes-without-justification**: Ensures test changes are documented

If a hook fails:

1. **Read the error message** - It explains what's wrong
2. **Fix the issue** - Don't bypass it
3. **Rerun the hook** - `uv run pre-commit run --all-files`
4. **For test changes**, include `TEST-CHANGE:` in your commit message body explaining why tests were added/modified

Example commit message with test justification (hook requires `TEST-CHANGE` in subject or body):

```
TEST-CHANGE: Add schema validation for plugin tools

Implements strict validation of plugin tool schemas.

Added test_plugin_schema.py to validate schema structure,
required for Web-UI dynamic form generation and MCP manifest creation.
```

**Phase 17 Test Log Requirement**:
For Phase 17 commits, test logs MUST be saved and referenced in commit messages:

```
feat(backend): Commit 1 - WebSocket Router + Endpoint Skeleton

Tests passed: 1211 passed, 10 warnings
Test log: /tmp/phase17_backend_commit_01_final.log
```

**Format required:**
- Include string `TEST-CHANGE` somewhere in `git log -1 --pretty=%B` output for test changes
- Include test log reference for Phase 17 commits
- Best practice: Start subject with `TEST-CHANGE:` for clarity
- Hook checks: `git log -1 --pretty=%B | grep -q "TEST-CHANGE"`

**Why this matters:**
- Bypassing hooks defeats their purpose
- Hooks prevent bad commits from reaching main
- Safety checks protect code quality and stability
- Test logs provide auditable proof of TDD compliance
- If you bypass a hook, the same issue will fail CI/CD anyway

### Skipped Tests Policy (Phase 7)

Skipped tests require APPROVAL with `APPROVED` comment on the next line:

```typescript
it.skip('some test description', () => {
  // APPROVED: Reason for skipping
  // ...
});
```

**Forbidden:** Never use `.only` in tests - it will be blocked by CI.

### Commit Message Format

```
<type>: <subject>

Types:
- feat: New feature
- fix: Bug fix
- refactor: Code restructuring
- test: Adding/updating tests
- docs: Documentation changes
- chore: Maintenance tasks
```

### Phase 17 Commit Message Format

Phase 17 commits should include test log references:

```
feat(backend): Commit 1 - WebSocket Router + Endpoint Skeleton

- Add WebSocket endpoint: /ws/video/stream
- Accept connection with pipeline_id query parameter
- Log connect/disconnect events (JSON structured logs)
- Reject connection if pipeline_id is missing
- Add is_valid_pipeline() to DagPipelineService and VideoFilePipelineService
- Register video_stream router in main.py
- Add comprehensive tests for WebSocket connection

Tests passed: 1211 passed, 10 warnings
Test log: /tmp/phase17_backend_commit_01_final.log

Phase 17: Real-Time Streaming Inference
```

---

## Project Milestones & Status

See `.ampcode/07_PROJECT_RECOVERY/ISSUES_LIST.md` for the latest project milestones and status.

**Current Active Milestones:**
- Milestone 1.5: YOLO Tracker Operational Baseline
- Milestone 2: Real Integration Tests
- Milestone 3: Unified Tool Execution (Frontend + Backend)
- Milestone 4: MCP Adapter Rewrite
- Milestone 5: Governance & Guardrails
- Milestone 6: Job-Based Pipeline & Web-UI Migration (Current Architecture)
- Milestone 7: VideoTracker Full Implementation (Job-Based Architecture)
- Milestone 8: Phase 7: CSS Modules Migration (NEW - Blocked until Phase 7 complete)
- **Phase 17: Real-Time Streaming Inference (IN PROGRESS - 4/12 backend commits completed)**

### Phase 17: Real-Time Streaming Inference

**Purpose**: Introduce real-time streaming layer on top of Phase-15/16 batch + async foundations

**Key Features**:
- WebSocket endpoint: `/ws/video/stream` for real-time frame processing
- Session manager: One session per connection with isolated state
- Real-time inference loop: frame → pipeline → result
- Backpressure: Drop frames / send slow-down signals to prevent overload
- Ephemeral results: No persistence, no job table

**Progress**:
- ✅ Commit 1: WebSocket Router + Endpoint Skeleton (5/5 tests passing)
- ✅ Commit 2: Session Manager Class (9/9 tests passing)
- ✅ Commit 3: Frame Validator (6/6 tests passing)
- ✅ Commit 4: Integrate SessionManager into WebSocket (4/4 tests passing)
- ⏳ Commit 5-12: Remaining backend commits (0/8 completed)

**Test Coverage**: 24/24 streaming tests passing

**Documentation**: See `.ampcode/04_PHASE_NOTES/Phase_17/` for detailed planning and Q&A

### Phase 17 Streaming Services API

**SessionManager** (`server/app/services/streaming/session_manager.py`):
```python
from app.services.streaming.session_manager import SessionManager

# Create session
session = SessionManager(pipeline_id="yolo_ocr")

# Track frames
session.increment_frame()
session.mark_drop()

# Calculate metrics
drop_rate = session.drop_rate()
should_drop = session.should_drop_frame(processing_time_ms=50.0)
should_slow = session.should_slow_down()

# Timing
current_time_ms = SessionManager.now_ms()
```

**FrameValidator** (`server/app/services/streaming/frame_validator.py`):
```python
from app.services.streaming.frame_validator import validate_jpeg, FrameValidationError

try:
    validate_jpeg(frame_bytes)
except FrameValidationError as e:
    print(f"Error: {e.code} - {e.detail}")
```

**Backpressure** (`server/app/services/streaming/backpressure.py`):
```python
from app.services.streaming.backpressure import Backpressure

# Check if frame should be dropped
should_drop = Backpressure.should_drop(
    processing_time_ms=50.0,
    drop_rate=0.15,
    drop_threshold=0.10
)

# Check if slow-down signal should be sent
should_slow = Backpressure.should_slow_down(
    drop_rate=0.35,
    slowdown_threshold=0.30
)
```

---

## Documentation Reference

Key documentation files for understanding the project:

- `ARCHITECTURE.md` - Overall system architecture
- `PLUGIN_DEVELOPMENT.md` - Plugin development guide
- `docs/design/execution-architecture.md` - Execution architecture details
- `docs/design/MCP.md` - MCP integration details
- `docs/design/PLUGIN_WEB_UI.md` - Plugin and Web-UI integration
- `docs/development/PYTHON_STANDARDS.md` - Python coding standards
- `docs/guides/PLUGIN_IMPLEMENTATION.md` - Plugin implementation guide

**Phase 17 Documentation** (Real-Time Streaming):
- `.ampcode/03_PLANS/Phase_17/PHASE_17_PLANS.md` - Complete Phase 17 plans
- `.ampcode/03_PLANS/Phase_17/PHASE_17_PROGRESS.md` - Progress tracking (4/12 backend commits completed)
- `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_OVERVIEW.md` - Phase 17 overview
- `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_BACKEND_USER_STORIES.md` - Backend user stories (12 commits)
- `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_FRONTEND_USER_STORIES` - Frontend user stories (8 commits)
- `.ampcode/04_PHASE_NOTES/Phase_17/PHASE_17_Q&A_01.md` through `PHASE_17_Q&A_04.md` - Q&A clarifications

Pre-commit runs in: .github/workflows/ci.yml

Job: lint (line 14-35)
Step: "Run pre-commit hooks" (line 29-30)
Uses pre-commit/action@v3.0.0 to run all hooks (black, ruff, mypy, eslint, etc.)
Web-UI tests run in:

Job: web-ui (line 85-116) in .github/workflows/ci.yml
Steps:
Line 103-106: npm run lint (ESLint)
Line 108-111: npm run type-check (TypeScript strict check)
Line 113-116: npm test -- --run (Vitest)
Both jobs depend on lint job completing first, and E2E tests depend on both test and web-ui.

Here's how to run each locally:

**1. execution-ci.yml:**
```bash
cd /home/rogermt/forgesyte
cd ../forgesyte-plugins  # Clone if needed: git clone --depth 1 https://github.com/rogermt/forgesyte-plugins.git
cd /home/rogermt/forgesyte/server && uv sync
python scripts/scan_execution_violations.py
uv run pytest tests/plugins -v
uv run pytest tests/execution -v
uv run pytest tests/ -v --tb=short
```

**2. governance-ci.yml:**
```bash
cd /home/rogermt/forgesyte/server && uv sync
uv run python tools/validate_plugins.py
uv run python tools/validate_pipelines.py
uv run python tools/generate_plugin_capability_matrix.py
git diff --exit-code docs/plugin_capability_matrix_generated.md
uv run pytest -q --disable-warnings --maxfail=1
```

**3. video_batch_validation.yml:**
```bash
cd /home/rogermt/forgesyte/server && uv sync
uv run python tools/validate_plugins.py
uv run python tools/validate_pipelines.py
uv run python tools/validate_video_batch_path.py
uv run pytest app/tests/video -q --maxfail=1
```

**4. vocabulary_validation.yml:** (already tested earlier)
```bash
cd /home/rogermt/forgesyte/server && uv sync
uv run python tools/vocabulary_scanner.py
uv run pytest tests/execution/test_vocabulary_scanner.py -v
# smoke test (start server, run smoke_test.py)
```