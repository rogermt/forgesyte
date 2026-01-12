# Test Coverage Setup

## Overview
This project enforces a minimum test coverage threshold of **80%** to ensure code quality and maintainability.

## Configuration

### pytest Configuration (pyproject.toml)
```toml
[tool.coverage.run]
source = ["app/"]
omit = ["*/tests/*", "*/conftest.py"]

[tool.coverage.report]
exclude_lines = [...]
fail_under = 80
precision = 2

[tool.coverage.html]
directory = "htmlcov"
```

### GitHub Actions Workflow
The `.github/workflows/lint-and-test.yml` now includes:
1. **Coverage collection** via `pytest --cov=app --cov-report=*` 
2. **Coverage reports**:
   - Terminal output with missing lines (`--cov-report=term-missing`)
   - XML for Codecov uploads
   - HTML report for detailed review
3. **Threshold enforcement**: `coverage report --fail-under=80`
4. **Codecov integration**: Fails build if upload fails

## Running Coverage Locally

### Full report with missing lines:
```bash
cd server
uv run pytest --cov=app --cov-report=term-missing
```

### HTML report for visualization:
```bash
cd server
uv run pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

### Check if coverage meets threshold:
```bash
cd server
uv run coverage report --fail-under=80
```

## Current Coverage
**Status**: 65.40% (below 80% threshold)

**Coverage by module**:
- app/__init__.py: 100%
- app/mcp_jsonrpc.py: 100%
- app/models.py: 100%
- app/mcp_adapter.py: 93.33%
- app/mcp_routes.py: 90.24%
- app/mcp_transport.py: 85.39%
- app/mcp_handlers.py: 80.60%
- app/auth.py: 52.50%
- app/plugin_loader.py: 57.48%
- app/api.py: 47.22%
- app/main.py: 49.47%
- app/tasks.py: 42.27%
- app/websocket_manager.py: 31.43%

## Next Steps
See `docs/work-tracking/REFACTORING_PLAN.md` Phase 3 (Test Coverage Analysis) to increase coverage to 80%+.

## CI/CD Behavior
- **Local commits**: Pre-commit hooks will run lint/format/type checks, but won't block on coverage
- **Pull requests**: GitHub Actions will:
  - Run all tests with coverage collection
  - Fail if coverage < 80%
  - Upload to Codecov for trend tracking
  - Display detailed coverage report in logs
- **Main branch merges**: Same as PR, but blocks merge if coverage insufficient

## Excluding Code from Coverage
Use `# pragma: no cover` comment to exclude specific lines:
```python
def debug_only_function():  # pragma: no cover
    print("Only for development")
```

Or exclude entire files via `omit` in configuration.
