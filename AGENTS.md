# Agent Commands and Conventions for ForgeSyte

This document defines essential commands and conventions for agents working on the ForgeSyte project.

## Project Overview

ForgeSyte is a modular AI-vision MCP server engineered for developers, featuring:
- **Server (Python/FastAPI)**: `/server` - Backend API, plugin management, job processing
- **Web-UI (React/TypeScript)**: `/web-ui` - Frontend client application
- **Plugin Architecture**: Modular vision analysis plugins (OCR, YOLO tracker, etc.)
- **Job-Based Pipeline**: Async job processing with `/v1/analyze` endpoint
- **MCP Integration**: Model Context Protocol for tool exposure
- **WebSocket Streaming**: Real-time video processing via `/v1/stream`

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
# CPU (CI): Tests OCR plugin only
uv run pytest tests/contract/ -v

# GPU (Kaggle): Tests all plugins including YOLO
RUN_MODEL_TESTS=1 uv run pytest tests/contract/ -v

# Run execution governance tests
uv run pytest tests/execution -v

# Run plugin registry tests
uv run pytest tests/plugins -v
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
│   ├── core/             # Core application logic
│   ├── examples/         # Example usage code
│   ├── logging/          # Logging configuration
│   ├── mcp/              # MCP (Model Context Protocol) implementation
│   ├── observability/    # Observability features
│   ├── plugins/          # Plugin system core
│   ├── realtime/         # Real-time processing
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic services
│   ├── main.py           # FastAPI application entry point
│   ├── models.py         # Database models
│   ├── routes_pipeline.py # Pipeline REST endpoints
│   └── websocket_manager.py # WebSocket handling
└── tests/
    ├── api/              # API endpoint tests
    ├── contract/         # Contract validation tests
    ├── execution/        # Execution governance tests
    └── plugins/          # Plugin tests
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
6. **Commit** - Only after all above pass

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

**Format required:**
- Include string `TEST-CHANGE` somewhere in `git log -1 --pretty=%B` output
- Best practice: Start subject with `TEST-CHANGE:` for clarity
- Hook checks: `git log -1 --pretty=%B | grep -q "TEST-CHANGE"`

**Why this matters:**
- Bypassing hooks defeats their purpose
- Hooks prevent bad commits from reaching main
- Safety checks protect code quality and stability
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