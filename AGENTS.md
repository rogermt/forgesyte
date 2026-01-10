# Agent Commands and Conventions

This document defines standard commands, workflows, and conventions for agents working on the Forgesyte project.

## Git Workflow

### Creating and Merging Branches

```bash
# Create a feature branch
git checkout -b feature-name

# Commit changes
git add .
git commit -m "Description of changes"

# Push to origin
git push origin feature-name

# Merge to main locally, then push
git checkout main
git merge feature-name
git push origin main
```

### Branch Naming

- Feature branches: `feature-name` or `feature/description`
- Bugfix branches: `fix-issue-name`
- Setup/init branches: `init-setup`
- Documentation: `docs-update`

### Important: Never Commit Directly to Main

All changes must go through a feature branch and be merged to main. Direct commits to main are strictly prohibited:

- Always create a feature branch for your work
- Make commits to the feature branch
- Push the feature branch to origin
- Merge to main locally and push after verification
- Never use `git push origin main` to push commits made directly on main

## Project Structure

- `/scratch/` - Temporary files and experiments (ignored in git)
- `/scripts/` - Utility scripts and automation
- `/docs/` - Generated documentation
- Root level docs: `README.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `PLUGIN_DEVELOPMENT.md`, `BRANDING.md`

## Python Conventions

### Environment

- Use `.venv/` for virtual environment
- Activate: `source .venv/bin/activate`
- Python 3.8+ required
- Use `uv` for running Python and managing dependencies (faster alternative to pip/venv)

### Running Python with uv

```bash
# Run a Python script
uv run script.py

# Run Python with arguments
uv run script.py --arg value

# Create/use virtual environment
uv venv

# Install dependencies
uv pip install package-name

# Sync dependencies from requirements.txt
uv sync
```

### Code Style

- Follow PEP 8
- Use type hints where practical
- Format with `black` (if configured)
- Lint with `ruff` (cache in `.ruff_cache/`)

### Linting and Type Checking

This project enforces strict code quality with automated tools:

**Setup (one-time)**:
```bash
uv pip install pre-commit
uv run pre-commit install
```

**Version pinning** - Versions matter for consistency:
- black==24.1.1
- ruff==0.9.1
- mypy==1.14.0
- types-Pillow (stub package for PIL type hints)

**Workflow before committing**:
1. **Black formatting** - Automatically formats code on commit
   - If files are modified, the commit fails - review changes and commit again
   - Runs automatically via pre-commit hook
2. **Ruff linting** - Checks for code quality issues
   - Run manually: `uv run ruff check --fix .`
   - Auto-fixes most issues (unused imports, trailing whitespace, etc.)
3. **Mypy type checking** - Enforces type safety
   - Run manually: `uv run mypy . --no-site-packages`
   - Use `cast()` from typing module for type inference issues
   - Add `# type: ignore[error-code]` only as last resort

**Common issues and fixes**:
- **"Undefined name" with Optional/Dict** - Add imports: `from typing import Optional, Dict, cast`
- **Generator type errors** - Use `cast(type, value)` for complex type inference
- **Missing type stubs** - Add to `additional_dependencies` in `.pre-commit-config.yaml`
- **Local/remote version mismatch** - Ensure `.pre-commit-config.yaml` versions match requirements-lint.txt

**Running locally before push** (required):
```bash
# Everything runs automatically on commit via pre-commit
# But you can manually run all hooks:
uv run pre-commit run --all-files

# Or individual tools:
uv run black . --exclude original_vision_mcp
uv run ruff check --fix . --exclude original_vision_mcp
uv run mypy . --exclude original_vision_mcp --no-site-packages
```

### Dependencies

- Document in `requirements.txt` or `pyproject.toml`
- Pin major versions for stability
- Use lock files for reproducibility

## ForgeSyte Python Development Standards

To ensure code is production-ready, maintainable, and resilient, all AI agents must adhere to the following standards when contributing to the **ForgeSyte** project.

### Core Principles

- **Prioritize Simplicity:** Write clean, readable, and maintainable code, avoiding unnecessary complexity.
- **Maintainability over Cleverness:** Choose obvious solutions over "clever" hacks to ensure long-term project health.
- **Self-Documenting Code:** Use meaningful variable and function names to reduce the need for excessive comments.

### Python Language Standards

- **Style Guidelines:** Strictly follow **PEP 8** style guidelines.
- **Type Safety:** Use **type hints** for all functions and modules. For monetary values, rates, or high-precision math, always use the **`Decimal` type** instead of floats to avoid precision errors.
- **Path Management:** Prefer **`pathlib`** over `os.path` for all file and directory operations.
- **Documentation:** Write comprehensive **docstrings** for all classes and functions.
- **Configuration:** Manage configuration via **environment variables** or configuration files (using Pydantic Settings) rather than hard-coding sensitive values.

```python
# Standard: Type hints, Decimal for currency, and input validation
from decimal import Decimal
from fastapi import Query
from pydantic import BaseModel

class Product(BaseModel):
    price: Decimal  # Financial precision

def process_payment(
    amount: Decimal = Query(..., gt=0),  # Validation guardrail
    currency_code: str = Query(..., min_length=3, max_length=3)
) -> None:
    pass
```

### Architectural Design & Patterns

- **Separation of Concerns:** Decouple the API layer from core logic by extracting business rules into **dedicated service classes**.
- **Decoupling with Protocols:** Leverage **Protocols** (structural typing) to define interfaces, ensuring components interact through contracts rather than concrete implementations.
- **The Registry Pattern:** Avoid long `if-elif` chains for algorithms or exporters. Use a **central registry** (dictionary or decorator-based) to map keys to behaviors, allowing for easy extensibility without modifying core code.
- **Composition over Inheritance:** Prefer composition or **mixins** to add functionality rather than creating brittle, deep inheritance hierarchies.
- **Avoid Singletons:** Do not use the Singleton pattern; Python **modules** are the idiomatic way to handle shared global state.

```python
# Standard: Registry Pattern to replace long if-elif chains
from typing import Callable

COMMAND_REGISTRY: dict[str, Callable] = {}

def register_command(name: str):
    def decorator(func: Callable):
        COMMAND_REGISTRY[name] = func
        return func
    return decorator

@register_command("export_pdf")
def export_to_pdf(data: dict):
    # logic here
    pass
```

### Resilience and Error Handling

- **The Retry Pattern:** Wrap all operations involving **external services, APIs, or LLMs** in retry logic to handle transient failures.
- **Exponential Backoff:** Implement retries with a delay that increases exponentially to prevent overloading a failing service.
- **Specific Exceptions:** Catch specific errors rather than using generic `try-except` blocks. Provide meaningful feedback, such as raising a **404 error** if a resource is missing.
- **Fallbacks:** Design systems with backup routes or default behaviors if a primary external call fails after all retry attempts.

```python
# Standard: Retry logic with exponential backoff using Tenacity
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_gemini_api(prompt: str):
    # This will automatically retry on transient network failures
    pass
```

### Performance and Observability

- **Structured Logging:** Replace all `print` statements with **logging** using Python's built-in `logging` module to allow for better monitoring and integration with services like Sentry.
- **Lazy Loading & Generators:** Use **generators (`yield`)** for large datasets to stream data row-by-row, keeping memory overhead low.
- **Strategic Caching:** Use `functools.cache` for expensive computations and implement **TTL (Time-To-Live) caches** for data that changes over time, like API-fetched exchange rates.
- **Health Checks:** Include a **`/health`** endpoint in all services so infrastructure (e.g., Kubernetes) can monitor availability.

### Testing Standards

- **Isolated Environments:** Use **in-memory databases** (like SQLite) for testing to ensure a clean setup and prevent pollution of production data.
- **Coverage Goals:** Aim for **80%+ test coverage**, ensuring success paths, invalid inputs, and edge cases are all verified.
- **Mocking:** Always mock external dependencies to ensure tests are fast and reliable.

### Development Workflow & Mandatory Tools

Before committing any code, the following tools must be run to ensure compliance:

1. **Formatting:** `black . && isort .`
2. **Linting:** `ruff check --fix .`
3. **Type Checking:** `mypy .`
4. **Testing:** `pytest`

## File Operations

### Reading Files
- Use `Read` tool for viewing complete files
- Use `Grep` for searching patterns
- Use `finder` for semantic code searches

### Creating/Editing Files
- Use `create_file` when replacing entire file contents
- Use `edit_file` for targeted changes to specific sections
- Always use absolute paths

### Formatting
- Run `format_file` after making large edits
- Respect existing code style

## Testing and Validation

- Run tests before committing: `pytest` or project-specific test command
- Check diagnostics: `get_diagnostics path/to/file`
- Validate git status before pushing

## Test-Driven Development (TDD)

TDD is the required development methodology for this project:

1. **Write tests first** - Before implementing any feature or fix, write failing tests that define the expected behavior
2. **Run and verify failure** - Confirm the tests fail before any implementation
3. **Implement code** - Write minimal code to make the tests pass
4. **Refactor** - Clean up and optimize code while keeping tests passing
5. **Commit after green tests** - Only commit when all tests pass

### Test File Conventions

- Test files: `test_*.py` or `*_test.py` in the same directory as code
- Use `pytest` framework and fixtures for test organization
- Use descriptive test names that explain the behavior being tested
- Aim for high test coverage (80%+ minimum)
- Include unit tests, integration tests, and edge cases

### Best Practices

- Write one assertion per test where possible
- Use fixtures for common test setup
- Mock external dependencies
- Test both success and failure paths
- Keep tests independent and idempotent

## Documentation

- Update relevant `.md` files when making architectural changes
- Keep `ARCHITECTURE.md` current with major changes
- Document new plugins in `PLUGIN_DEVELOPMENT.md`
- Update `CONTRIBUTING.md` if development workflow changes

## Common Issues

### Ignored Directories

The following are intentionally ignored and should not be committed:
- `__pycache__/`
- `.venv/`, `venv/`, `env/`
- `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`
- `build/`, `dist/`, `*.egg-info/`
- `scratch/`
- `.vscode/`, `.idea/` (if present locally)

### Before Pushing

1. Verify `git status` is clean or changes are staged
2. Run relevant tests
3. Check for large files (> 100MB shouldn't be committed)
4. Ensure commit messages are descriptive
5. Pull latest changes if merging to main

## Unit Work & Context Management

Large tasks are broken into small work units (1-2 hours each) to respect AI context limits. Each work unit follows this workflow:

### Work Unit Lifecycle

1. **Start Unit**: Read docs/work-tracking/Progress.md to understand current status
2. **Do Work**: Complete the specific tasks for the work unit
3. **Test**: Run verification commands to confirm acceptance criteria
4. **Commit**: Make atomic commit with conventional message (feat:, refactor:, etc.)
5. **Document Learnings**: Update docs/work-tracking/Learnings.md with:
   - What was learned during implementation
   - Unexpected issues encountered
   - Decisions made and rationale
   - Tips for next similar work unit
   - Any blockers or dependencies discovered
6. **Update Progress**: Update docs/work-tracking/Progress.md with:
   - Mark completed unit as done with timestamp
   - Update current context usage
   - Note any blockers or changed estimates
   - List what unit is ready for next session

7. **Thread Boundary**: When context reaches 70-80% usage, the current thread ends
   - Next thread begins with updated Progress.md and Learnings.md as context
   - No need to re-explain completed work
   - Next agent continues from exact point

### Documentation Files

**docs/work-tracking/Progress.md**:
- Current work unit status (in progress, done, blocked, todo)
- Timestamp when each unit started and completed
- Estimated vs actual time spent
- Any blockers or dependencies
- Context usage meter
- Next recommended work unit

**docs/work-tracking/Learnings.md**:
- What was learned in each work unit
- Unexpected issues and solutions
- Code patterns discovered
- Integration points and gotchas
- Tips for future similar work
- Architecture insights

### Progress.md Format

```markdown
# TypeScript Migration Progress

**Last Updated**: [timestamp]
**Current Context Usage**: [50%]
**Overall Progress**: [12/22 units completed]

## Work Unit Status

### Completed
- [x] WU-01: Extract package.json (2 hours, completed [time])
- [x] WU-02: Extract TypeScript config (1.5 hours, completed [time])

### In Progress
- [ ] WU-03: Extract Vite config (45 min elapsed, 0 blockers)

### Blocked
- [ ] WU-15: JobList API integration (blocked on WU-11 completion)

### Todo
- [ ] WU-04: Extract React components
- [ ] WU-05: Extract hooks and API client

## Current Work Unit: WU-03
- **Status**: In Progress
- **Time Elapsed**: 45 minutes
- **Blockers**: None
- **Next Steps**: Extract vite.config.ts and index.html from code2.md

## Notes for Next Session
- WU-03 is 75% complete, needs 15 more minutes
- WU-01 and WU-02 both validated successfully
- No major blockers discovered so far
```

### Learnings.md Format

Each work unit should have a dedicated section following this structure:

```markdown
## WU-XX: Brief Description

**Completed**: YYYY-MM-DD HH:MM  
**Duration**: X hours  
**Status**: ✅ Complete

### What Went Well
- Item 1 (keep concise, 1 line)
- Item 2
- Item 3
- Item 4
- Item 5
- Item 6

### Challenges & Solutions
- **Issue**: Problem encountered
  - **Solution**: How it was resolved
- **Issue**: Another problem
  - **Solution**: How it was resolved
- **Issue**: Third problem
  - **Solution**: How it was resolved

### Key Insights
- Insight 1 (technical understanding gained)
- Insight 2
- Insight 3
- Insight 4
- Insight 5
- Insight 6

### Architecture Decisions
- **Decision 1**: Explanation of choice made
- **Decision 2**: Why this approach was chosen
- **Decision 3**: Trade-off analysis
- **Decision 4**: Design pattern selected
- **Decision 5**: Integration approach

### Tips for Similar Work
- Actionable tip 1
- Actionable tip 2
- Actionable tip 3
- Actionable tip 4
- Actionable tip 5
- Actionable tip 6

### Blockers Found
- None (or list items that blocked progress)
```

**Format Rules**:
- **What Went Well**: 6 items, concise, one-liners
- **Challenges & Solutions**: 3 items, detailed explanations with issue/solution pairs
- **Key Insights**: 6 items, technical learnings for future reference
- **Architecture Decisions**: 5 items, explain design choices and trade-offs
- **Tips for Similar Work**: 6 items, actionable guidance for future units
- **Blockers Found**: List any items that blocked progress or note "None"

**Do NOT include**:
- Test coverage breakdown
- Files created/modified listing (use git commits for this)
- Test results summary (they're captured in CI)
- Next steps (use Progress.md instead)

### At Work Unit Completion

Before marking a unit done, always:

```bash
# 1. Run verification commands from unit
npm run build        # if applicable
npm run type-check   # if applicable
npm test             # if applicable

# 2. Check git status
git status
git diff

# 3. Create atomic commit
git add .
git commit -m "feat: Complete WU-XX - [description]"

# 4. Update Learnings.md
# Add section for this work unit with:
# - What was learned
# - Unexpected issues
# - Decisions made
# - Tips for similar work
# - Any blockers

# 5. Update Progress.md
# - Mark unit as complete with timestamp
# - Update context usage
# - Note next recommended unit
# - List any changed blockers

# 6. Verify no uncommitted changes
git status  # Should show clean working directory
```

### Context Limit Management

- **Current Thread Limit**: 200k tokens
- **Safe Stopping Point**: 160k tokens (80%)
- **When Approaching Limit**:
  1. Finish current work unit
  2. Make final commit with all changes
  3. Update Progress.md with current status
  4. Update Learnings.md with findings
  5. End thread gracefully

- **Next Thread Start**:
  1. Read Progress.md and Learnings.md first
  2. Continue with next work unit in queue
  3. No re-explanation needed
  4. Build on previously documented learnings

## Quick Reference

| Command | Purpose |
|---------|---------|
| `git status` | Check current branch and changes |
| `git log --oneline -n 10` | View recent commits |
| `git diff` | See unstaged changes |
| `git stash` | Temporarily save changes |
| `source .venv/bin/activate` | Activate Python environment |
| `pytest` | Run tests (if configured) |
