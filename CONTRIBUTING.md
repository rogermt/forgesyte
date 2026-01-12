# Contributing to ForgeSyte

Thank you for contributing to ForgeSyte. This project values clarity, modularity, and reproducibility. Contributions that strengthen those qualities are especially welcome.

---

## Development Environment

### Backend (uv)

```bash
cd server
uv sync
uv run fastapi dev app/main.py
```

### Frontend (React)

```bash
cd web-ui
npm install
npm run dev
```

---

## Branching Strategy

- `main` — stable  
- `develop` — active development  
- `feature/<name>` — new features  

---

## Code Style

### Python
- Use `uvx ruff format` for formatting  
- Use type hints  
- Keep plugin contracts explicit  

### React/TypeScript
- Use Prettier  
- Prefer explicit types  

---

## Testing Strategy

### Running Tests

Backend:

```bash
cd server
uv run pytest
```

Frontend:

```bash
cd web-ui
npm test
```

### Mock Data and API Contracts

This project follows **schema-driven mock data practices** to ensure test mocks always match real API responses.

**Key Principle**: Never hand-write mock objects. Use factory functions or golden fixtures instead.

**Files**:
- **Golden Fixtures**: `fixtures/api-responses.json` — Real API response examples
- **TypeScript Factories**: `web-ui/src/test-utils/factories.ts` — Type-safe mock generators
- **Sync Script**: `scripts/sync-fixtures.sh` — Automated fixture update tool

### Using Mock Factories in Web UI Tests

```typescript
// ✅ CORRECT: Use factory functions
import { createMockJob } from '../../test-utils/factories';

it('should display job', () => {
  const mockJob = createMockJob({ status: 'done' });
  // Test with generated mock
});

// ❌ INCORRECT: Hand-written mocks
const mockJob = { id: '123', status: 'processing' };
```

### Golden Fixtures

Fixtures in `fixtures/api-responses.json` serve as the source of truth for API response shapes:

```python
# test_api_contracts.py
import json
from pathlib import Path

fixtures_path = Path(__file__).parent.parent / 'fixtures' / 'api-responses.json'
with open(fixtures_path) as f:
    FIXTURES = json.load(f)

def test_jobs_endpoint(client):
    """Verify real API response matches fixture"""
    response = client.get('/v1/jobs?limit=10')
    expected = FIXTURES['jobs_list']
    assert response.json() == expected
```

### Synchronizing Fixtures When API Changes

When API endpoints change, update fixtures automatically:

```bash
# Ensure server dependencies are installed
cd server
uv sync

# Run from project root
./scripts/sync-fixtures.sh
```

This script:
1. Starts a local test server
2. Calls all real API endpoints
3. Captures responses to `fixtures/api-responses.json`
4. Validates JSON structure
5. Creates a backup of previous fixtures

The updated fixtures are committed and used across all tests.

### Integration Tests

Integration tests verify that real API responses match documented contracts:

```python
# server/tests/integration/test_api_contracts.py
@pytest.mark.integration
async def test_jobs_endpoint_response_shape(client):
    """Verify /v1/jobs returns documented schema"""
    response = await client.get("/v1/jobs?limit=10")
    data = response.json()
    
    # Assert schema matches JobResponse model
    assert "jobs" in data
    assert "count" in data
    for job in data["jobs"]:
        assert "job_id" in job  # Not "id"
        assert job["status"] in ["queued", "running", "done", "error", "not_found"]
        assert "created_at" in job
        assert "completed_at" in job
```

### Checklist for Adding Tests

When adding new tests, ensure:

- [ ] Use mock factories instead of hand-written mocks
- [ ] Mock field names match API response exactly
- [ ] Mock enum values match server enums (not guesses)
- [ ] Integration tests verify API contracts
- [ ] Update fixtures if API changes: `./scripts/sync-fixtures.sh`
- [ ] All tests pass: `npm test` and `pytest`
- [ ] Coverage maintained at 80%+

### Related Documentation

See `AGENTS.md` for detailed mock best practices and testing patterns.

---

## Pull Requests

Include:

- What changed  
- Why  
- How to test  
- Any breaking changes  

---

## Adding Plugins

See `PLUGIN_DEVELOPMENT.md`.

Plugins must:

- Implement `Plugin` class  
- Provide `metadata()`  
- Provide `analyze()`  
- Avoid heavy dependencies unless necessary  
