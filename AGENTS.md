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

```bash
# Create feature branch
git checkout -b feature-name

# Commit changes
git add .
git commit -m "feat: description"

# Push and create PR
git push origin feature-name
gh pr create --base main --head feature-name --title "feat: description"
```
