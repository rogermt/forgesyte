# Agent Commands and Conventions for ForgeSyte

This document defines essential commands and conventions for agents working on the ForgeSyte project.

## Project Overview

- **Server (Python/FastAPI)**: `/server` - Backend API, plugin management, job processing
- **Web-UI (React/TypeScript)**: `/web-ui` - Frontend client application

---

## Python Server (Backend)

All commands run from the `server/` directory.

### Setup and Dependencies

```bash
cd server

# Sync dependencies
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
# Run all tests
npm run test

# Run tests once (no watch mode)
npm run test -- --run

# Run a single test file
npm run test -- src/api/client.test.ts

# Type check
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
| `.pre-commit-config.yaml` | Pre-commit hooks (black, ruff, mypy) |
| `web-ui/tsconfig.json` | TypeScript strict mode config |
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
5. **Run lint and type check** - Ensure code quality
6. **Commit** - Only after all above pass

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

For latest progress in the project see issues list to recoveer the project from LLM agents who never follow instruction just maake things up and expect things to work  /home/rogermt/forgesyte/docs/issues/ISSUES_LIST.md
