# API Response Fixtures

This directory contains golden fixture files - real API response examples that serve as the source of truth for test mock data.

## Purpose

Golden fixtures ensure that:
- Test mocks match actual API response shapes
- Field names and types are consistent
- Enum values match server-side definitions
- Integration tests can verify contracts

## Files

### `api-responses.json`

Complete collection of API responses used across tests. Each key maps to a specific API endpoint or use case.

**Contents:**

| Key | Source Endpoint | Usage |
|-----|-----------------|-------|
| `jobs_list` | `GET /v1/jobs?limit=10` | JobList component tests, list jobs scenarios |
| `job_single` | `GET /v1/jobs/{id}` | ResultsPanel component tests, single job detail |
| `plugins_list` | `GET /v1/plugins` | PluginSelector component tests |
| `frame_result` | WebSocket `/v1/stream` payload | useWebSocket hook tests, frame result handling |
| `health` | `GET /v1/health` | Health check tests |

## Usage in Tests

### TypeScript/React Tests

```typescript
import fixturesData from '../fixtures/api-responses.json';

describe('JobList', () => {
  it('should render jobs from API', () => {
    const mockJobs = fixturesData.jobs_list.jobs;
    // Use fixture directly
    mockApiClient.listJobs.mockResolvedValue(mockJobs);
  });
});
```

### Python Tests

```python
import json
from pathlib import Path

def load_fixtures():
    fixtures_path = Path(__file__).parent.parent / 'fixtures' / 'api-responses.json'
    with open(fixtures_path) as f:
        return json.load(f)

FIXTURES = load_fixtures()

def test_jobs_endpoint():
    expected_jobs = FIXTURES['jobs_list']['jobs']
```

## Updating Fixtures

When API responses change, fixtures must be updated to match:

```bash
# Option 1: Automated synchronization (recommended)
./scripts/sync-fixtures.sh

# Option 2: Manual update
# 1. Start server: npm run dev (backend)
# 2. Call API endpoint and copy response
# 3. Update corresponding key in api-responses.json
# 4. Verify all tests still pass: npm test && pytest
```

## Schema Validation

Each fixture must match its corresponding Pydantic model:

**JobResponse** (`server/app/models.py:46`)
```python
job_id: str              # UUID
status: JobStatus       # "queued" | "running" | "done" | "error" | "not_found"
created_at: datetime    # ISO 8601
completed_at: Optional[datetime]
result: Optional[Dict]
error: Optional[str]
progress: Optional[float]  # 0-100
```

**FrameResult** (`web-ui/src/hooks/useWebSocket.ts:21`)
```typescript
frame_id: string;
plugin: string;
result: Record<string, unknown>;
processing_time_ms: number;
```

**Plugin** (`server/app/models.py:78`)
```python
name: str
description: str
version: str
inputs: List[str]
outputs: List[str]
permissions: List[str]
config_schema: Optional[Dict]
```

## Fixture Status

| Fixture | Last Updated | Source |
|---------|--------------|--------|
| jobs_list | 2026-01-12 | Real server responses |
| job_single | 2026-01-12 | Real server responses |
| plugins_list | 2026-01-12 | Real server responses |
| frame_result | 2026-01-12 | Real WebSocket payload |
| health | 2026-01-12 | Real server responses |

## Testing Against Fixtures

All tests should use fixtures, not hand-written mocks:

```typescript
// ❌ Don't do this
const mockJob = { id: '123', status: 'processing' };

// ✅ Do this
import fixtures from '../fixtures/api-responses.json';
const mockJob = fixtures.jobs_list.jobs[0];
```

## Contract Verification

Integration tests verify that real API responses match fixtures:

```python
# server/tests/integration/test_api_contracts.py
def test_jobs_endpoint_matches_fixture(client):
    """Real API response must match fixture schema"""
    response = client.get('/v1/jobs?limit=10')
    real_data = response.json()
    
    expected_fixture = FIXTURES['jobs_list']
    assert_schema_matches(real_data, expected_fixture)
```

## Related Files

- **AGENTS.md** - Mock best practices documentation
- **TESTING.md** - Testing guide and examples
- **scripts/sync-fixtures.sh** - Automated fixture synchronization
- **.gitignore** - Fixtures are committed (source of truth)
