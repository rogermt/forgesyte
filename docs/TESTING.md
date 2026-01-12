# Testing Guide for ForgeSyte

This document provides comprehensive guidance on testing in ForgeSyte, with emphasis on mock data best practices and API contract verification.

## Overview

The ForgeSyte testing strategy ensures test mocks always match real API responses through:

- **Golden Fixtures**: Real API response examples stored in version control
- **Schema-Driven Factories**: Type-safe mock generators for TypeScript
- **Integration Tests**: Automated verification that API responses match contracts
- **Fixture Synchronization**: Automated script to update mocks when API changes

---

## Running Tests

### Backend (Python/FastAPI)

```bash
cd server
uv sync
uv run pytest                           # Run all tests
uv run pytest tests/unit/               # Run unit tests only
uv run pytest tests/integration/        # Run integration tests only
uv run pytest -v                        # Verbose output
uv run pytest --cov=app                 # Generate coverage report
uv run coverage report --fail-under=80  # Verify 80% coverage threshold
```

### Frontend (React/TypeScript)

```bash
cd web-ui
npm test                    # Run all tests (watch mode)
npm run test:ci             # Run tests once (for CI)
npm run test:coverage       # Generate coverage report
npm run type-check          # TypeScript type checking
npm run lint                # ESLint
npm run build               # Verify build succeeds
```

### End-to-End Testing

```bash
cd /path/to/forgesyte
./e2e.test.sh  # Tests server and web-ui together
```

---

## Mock Data Best Practices

The principle is simple: **Never hand-write mock objects.** Use factory functions or golden fixtures instead.

### Why This Matters

Hand-written mocks diverge from reality:

```typescript
// ❌ BAD: Hand-written mock with field name mistakes
const mockJob = {
  id: "123",                    // ❌ Should be job_id
  status: "processing",         // ❌ Should be "running" or "queued"
  updated_at: "2024-01-01",     // ❌ Should be completed_at
};

// ✅ GOOD: Factory function from actual API schema
const mockJob = createMockJob({ status: "queued" });
```

The problem: Tests pass with wrong field names, then code breaks in production.

### Option 1: Schema-Driven Factories (Recommended for TypeScript)

Use factory functions generated from actual TypeScript interfaces:

```typescript
// src/test-utils/factories.ts
import { Job, Plugin, FrameResult } from "../types/api";

export function createMockJob(overrides?: Partial<Job>): Job {
  return {
    job_id: "550e8400-e29b-41d4-a716-446655440000",
    plugin: "motion_detector",
    status: "queued",
    created_at: "2024-01-01T00:00:00Z",
    completed_at: null,
    progress: 0,
    result: null,
    error: null,
    ...overrides,
  };
}

export function createMockPlugin(overrides?: Partial<Plugin>): Plugin {
  return {
    id: "motion_detector",
    name: "Motion Detector",
    version: "1.0.0",
    description: "Detects motion in images",
    schema: {},
    ...overrides,
  };
}
```

Usage in tests:

```typescript
// components/__tests__/JobList.test.tsx
import { createMockJob } from "../../test-utils/factories";

describe("JobList", () => {
  it("should display job with done status", () => {
    const mockJob = createMockJob({ status: "done" });
    // Mock automatically has correct field names and types
  });

  it("should handle error status", () => {
    const mockJob = createMockJob({
      status: "error",
      error: "Plugin failed",
    });
    // Partial overrides while maintaining type safety
  });
});
```

Benefits:
- Type-safe: TypeScript catches field name mistakes at compile time
- Maintainable: Central location for all factories
- Verifiable: Factories derive from actual API types
- Testable: Factory functions themselves can be tested

### Option 2: Golden Fixtures (Recommended for Python)

Store real API responses as JSON fixtures:

```json
// fixtures/api-responses.json
{
  "jobs_list": {
    "jobs": [
      {
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "plugin": "motion_detector",
        "status": "done",
        "created_at": "2024-01-01T00:00:00Z",
        "completed_at": "2024-01-01T00:01:00Z",
        "progress": 100,
        "result": { "motion_detected": true },
        "error": null
      }
    ],
    "count": 1
  },
  "plugins_list": {
    "plugins": [
      {
        "id": "motion_detector",
        "name": "Motion Detector",
        "version": "1.0.0",
        "description": "Detects motion in images",
        "schema": {}
      }
    ],
    "count": 1
  }
}
```

Usage in tests:

```python
# tests/unit/test_job_service.py
import json
from pathlib import Path

# Load fixtures once at module level
FIXTURES_PATH = Path(__file__).parent.parent.parent / "fixtures" / "api-responses.json"
with open(FIXTURES_PATH) as f:
    FIXTURES = json.load(f)

def test_list_jobs_with_done_status(mock_job_store):
    """Verify job service handles done status correctly."""
    # Use fixture as mock data
    mock_job_store.list.return_value = FIXTURES["jobs_list"]["jobs"]
    
    jobs = service.list_jobs()
    
    assert len(jobs) == 1
    assert jobs[0]["job_id"] == "550e8400-e29b-41d4-a716-446655440000"
    assert jobs[0]["status"] == "done"
```

Benefits:
- Language-agnostic: Same fixtures used across Python and TypeScript
- Real data: Captured from actual API responses
- Traceable: Easy to see which endpoints provided the fixture
- Auditable: Golden fixtures tracked in version control

### Option 3: Integration Tests (Verify Contracts)

Write tests that verify real API responses match your expectations:

```python
# tests/integration/test_api_contracts.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import JobResponse

client = TestClient(app)

@pytest.mark.integration
def test_jobs_endpoint_response_shape():
    """Verify /v1/jobs returns documented schema."""
    response = client.get("/v1/jobs?limit=10")
    assert response.status_code == 200
    
    data = response.json()
    
    # Assert top-level structure
    assert "jobs" in data
    assert "count" in data
    assert isinstance(data["jobs"], list)
    
    # Assert each job has correct fields
    for job in data["jobs"]:
        assert "job_id" in job        # Not "id"
        assert "status" in job
        assert "created_at" in job
        assert "completed_at" in job
        
        # Validate enum values
        assert job["status"] in [
            "queued", "running", "done", "error", "not_found"
        ]
```

Benefits:
- Real verification: Tests against actual API implementation
- Catches drift: Integration tests fail if API shape changes
- Production confidence: Tests prove mocks match reality
- Documentation: Test assertions document API contracts

---

## API Contract Testing

API contract testing ensures your code's assumptions about the API match reality.

### The Problem

```
┌─────────────────┐
│  Test with      │
│  hand-written   │  ✅ Tests pass
│  mocks          │
└─────────────────┘
         ↓
    Code assumes:
    - job has "id" field
    - status is "processing"
    - error is "error_message"
         ↓
┌─────────────────┐
│  Real API       │
│  actually has:  │  ❌ Code fails
│  - job_id       │
│  - status is    │
│    "queued"     │
│  - error is null│
└─────────────────┘
```

### The Solution

Create integration tests that verify real API responses:

```python
# tests/integration/test_api_contracts.py
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import JobResponse, PluginMetadata

FIXTURES_PATH = Path(__file__).parent.parent.parent / "fixtures" / "api-responses.json"
with open(FIXTURES_PATH) as f:
    FIXTURES = json.load(f)

client = TestClient(app)

@pytest.mark.integration
class TestJobsEndpointContract:
    """Verify /v1/jobs and /v1/jobs/{id} match documented contracts."""
    
    def test_jobs_list_endpoint(self):
        """GET /v1/jobs returns JobListResponse schema."""
        response = client.get("/v1/jobs?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify structure
        assert "jobs" in data
        assert "count" in data
        
        # Verify each job matches JobResponse schema
        for job in data["jobs"]:
            # Required fields
            assert "job_id" in job
            assert "plugin" in job
            assert "status" in job
            assert "created_at" in job
            assert "completed_at" in job
            
            # Field types and values
            assert isinstance(job["job_id"], str)
            assert job["status"] in ["queued", "running", "done", "error", "not_found"]
    
    def test_single_job_endpoint(self):
        """GET /v1/jobs/{job_id} returns JobResponse schema."""
        # Create a job first
        response = client.get("/v1/jobs?limit=1")
        jobs = response.json()["jobs"]
        if not jobs:
            pytest.skip("No jobs available for testing")
        
        job_id = jobs[0]["job_id"]
        
        # Fetch single job
        response = client.get(f"/v1/jobs/{job_id}")
        assert response.status_code == 200
        
        job = response.json()
        
        # Verify contract
        assert job["job_id"] == job_id
        assert all(field in job for field in [
            "job_id", "plugin", "status", "created_at", "completed_at"
        ])

@pytest.mark.integration
class TestPluginsEndpointContract:
    """Verify /v1/plugins matches documented contract."""
    
    def test_plugins_endpoint(self):
        """GET /v1/plugins returns list of PluginMetadata."""
        response = client.get("/v1/plugins")
        assert response.status_code == 200
        
        data = response.json()
        assert "plugins" in data
        
        for plugin in data["plugins"]:
            # Required fields per PluginMetadata
            assert "id" in plugin
            assert "name" in plugin
            assert "version" in plugin
            assert "schema" in plugin
```

### Contract Testing Checklist

- [ ] Test all documented endpoints
- [ ] Verify required vs optional fields
- [ ] Check enum/status values match definitions
- [ ] Test error responses (404, 422, 500)
- [ ] Parametrize tests for all status variants
- [ ] Compare against golden fixtures
- [ ] Run tests in CI against real server

---

## Golden Fixtures

Golden fixtures are your source of truth for API response shapes.

### Where They're Stored

```
forgesyte/
├── fixtures/
│   ├── README.md              # Fixture documentation
│   └── api-responses.json     # Real API responses
├── server/
│   └── tests/
│       └── integration/
│           └── test_api_contracts.py
└── web-ui/
    └── src/
        ├── test-utils/
        │   └── factories.ts
        └── components/
            └── __tests__/
```

### Fixture Format

```json
{
  "jobs_list": {
    "description": "Response from GET /v1/jobs",
    "jobs": [ ... ],
    "count": 1
  },
  "job_single": {
    "description": "Response from GET /v1/jobs/{id}",
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    ...
  },
  "plugins_list": {
    "description": "Response from GET /v1/plugins",
    "plugins": [ ... ],
    "count": 1
  }
}
```

### Syncing Fixtures When API Changes

When you modify API endpoints, update fixtures automatically:

```bash
# From project root
cd server
uv sync
cd ..

./scripts/sync-fixtures.sh
```

This script:
1. Starts a local test server
2. Calls all real API endpoints
3. Captures responses to `fixtures/api-responses.json`
4. Validates JSON structure
5. Creates timestamped backup of previous fixtures
6. Commits updated fixtures to git

### Using Fixtures in Tests

Python:
```python
import json
from pathlib import Path

FIXTURES = json.load(open(Path(__file__).parent / "fixtures" / "api-responses.json"))

def test_something():
    expected = FIXTURES["jobs_list"]
    # Use as mock data or comparison
```

TypeScript:
```typescript
import fixtures from "../../fixtures/api-responses.json";

it("matches fixture shape", () => {
  const mockJob = createMockJob();
  // Verify against fixture structure
  expect(mockJob).toMatchObject(fixtures.jobs_list.jobs[0]);
});
```

---

## Examples

### Example 1: Testing a Component with Factory Mocks

```typescript
// JobList.test.tsx
import { render, screen } from "@testing-library/react";
import { createMockJob } from "../../test-utils/factories";
import JobList from "./JobList";

describe("JobList", () => {
  it("should display completed jobs", () => {
    const mockJobs = [
      createMockJob({ job_id: "job-1", status: "done" }),
      createMockJob({ job_id: "job-2", status: "done" }),
    ];

    render(<JobList jobs={mockJobs} />);

    expect(screen.getByText("job-1")).toBeInTheDocument();
    expect(screen.getByText("job-2")).toBeInTheDocument();
  });

  it("should show error status with message", () => {
    const mockJob = createMockJob({
      status: "error",
      error: "Plugin failed to initialize",
    });

    render(<JobList jobs={[mockJob]} />);

    expect(screen.getByText("Plugin failed to initialize")).toBeInTheDocument();
  });

  it("should display progress for running jobs", () => {
    const mockJob = createMockJob({
      status: "running",
      progress: 45,
    });

    render(<JobList jobs={[mockJob]} />);

    expect(screen.getByText("45%")).toBeInTheDocument();
  });
});
```

### Example 2: Integration Test Verifying API Contract

```python
# tests/integration/test_api_contracts.py
@pytest.mark.integration
def test_job_creation_and_retrieval():
    """Verify job can be created and retrieved with correct shape."""
    
    # Create job
    create_response = client.post(
        "/v1/jobs",
        json={"plugin": "motion_detector", "image": "base64..."}
    )
    assert create_response.status_code == 201
    created_job = create_response.json()
    
    # Verify created job has all required fields
    assert "job_id" in created_job
    assert created_job["status"] == "queued"
    assert created_job["created_at"] is not None
    
    # Retrieve job
    job_id = created_job["job_id"]
    retrieve_response = client.get(f"/v1/jobs/{job_id}")
    assert retrieve_response.status_code == 200
    
    retrieved_job = retrieve_response.json()
    
    # Verify retrieved job matches fixture structure
    assert retrieved_job == created_job
```

### Example 3: Testing WebSocket Integration

```typescript
// useWebSocket.test.ts
import { renderHook, act, waitFor } from "@testing-library/react";
import { createMockFrameResult } from "../../test-utils/factories";
import { useWebSocket } from "./useWebSocket";

describe("useWebSocket", () => {
  it("should process frame results from server", async () => {
    const mockResult = createMockFrameResult({
      tool_name: "motion_detector",
      status: "success",
    });

    // Mock WebSocket with frame result
    global.WebSocket = vi.fn(() => ({
      send: vi.fn(),
      close: vi.fn(),
      addEventListener: vi.fn((event, handler) => {
        if (event === "message") {
          // Simulate server sending frame result
          handler({ data: JSON.stringify(mockResult) });
        }
      }),
    }));

    const { result } = renderHook(() => useWebSocket({ url: "ws://localhost" }));

    await waitFor(() => {
      expect(result.current.lastMessage).toEqual(mockResult);
    });
  });
});
```

---

## Troubleshooting

### Problem: "Tests Pass But Code Fails in Production"

**Symptom**: All your tests pass locally, but code fails when running against real API.

**Root Cause**: Mock data doesn't match real API responses.

**Solution Checklist**:

```typescript
// 1. Verify mock field names match API
const mockJob = createMockJob();
// ✅ Has job_id (not id)
// ✅ Has status (not state)
// ✅ Has completed_at (not updated_at)

// 2. Verify enum values
assert(["queued", "running", "done", "error"].includes(mockJob.status));
// ✅ Don't use "processing" (server uses "running")

// 3. Compare against golden fixtures
import fixtures from "../../fixtures/api-responses.json";
const fixtureJob = fixtures.jobs_list.jobs[0];
assert(Object.keys(mockJob).sort() === Object.keys(fixtureJob).sort());
// ✅ Field names match exactly

// 4. Run integration tests
// npm run test:integration
// ✅ Real API verification
```

### Problem: "Mock Factory Not Found"

**Symptom**: Import error when trying to use `createMockJob()`.

**Solution**:

1. Check that `web-ui/src/test-utils/factories.ts` exists
2. Verify factory is exported: `export function createMockJob(...)`
3. Import correctly: `import { createMockJob } from "../../test-utils/factories"`

### Problem: "Tests Pass Differently Locally vs CI"

**Symptom**: Tests pass locally but fail in CI pipeline.

**Root Cause**: Mock data differs between environments, or fixtures not synced.

**Solution**:

```bash
# 1. Sync fixtures to latest API
./scripts/sync-fixtures.sh

# 2. Regenerate factories from fixtures
# (Factories should be automatically synced)

# 3. Run tests exactly as CI does
cd web-ui
npm run lint
npm run type-check
npm run test:ci
npm run build

cd ../server
uv sync
PYTHONPATH=. uv run mypy app/ --no-site-packages
uv run pytest --cov=app
```

### Problem: "Mocking Doesn't Work (Component Uses Real API)"

**Symptom**: Component calls real API even though you mocked it.

**Root Cause**: Mock not set up before component renders, or mock module incorrect.

**Solution**:

```typescript
// ✅ CORRECT: Mock before component import
vi.mock("../../hooks/useAPI", () => ({
  useAPI: vi.fn(() => ({ data: mockData })),
}));

import { MyComponent } from "./MyComponent";

it("should use mocked API", () => {
  render(<MyComponent />);
  // Mock is active before component renders
});

// ❌ WRONG: Mock after component import
import { MyComponent } from "./MyComponent";
vi.mock("../../hooks/useAPI", () => ({
  useAPI: vi.fn(() => ({ data: mockData })),
}));
// Too late - module already imported
```

### Problem: "Can't Update Fixtures (sync-fixtures.sh Fails)"

**Symptom**: `./scripts/sync-fixtures.sh` exits with error.

**Solution**:

```bash
# 1. Check server is installable
cd server
uv sync
uv run fastapi dev app/main.py
# Ctrl+C when server starts

# 2. Check server dependencies are correct
cd server
uv pip list | grep fastapi

# 3. Run sync script with verbose output
cd ..
bash -x ./scripts/sync-fixtures.sh
```

---

## Mock Data Verification Checklist

Before committing tests with mocks:

- [ ] **Field Names Match API**
  - Use factories or golden fixtures, not hand-written objects
  - Grep for anti-patterns: `{ id:` should be `{ job_id:`

- [ ] **Enum Values Match**
  - Status values match server: `["queued", "running", "done", "error"]`
  - Test all variants via factory overrides

- [ ] **Required vs Optional Fields**
  - All required fields present in mocks
  - Optional fields nullable or omitted

- [ ] **Integration Tests Verify**
  - Run tests against real API server
  - Assertions match golden fixtures

- [ ] **Coverage Maintained**
  - Before: `npm run test:coverage` or `pytest --cov`
  - After: Verify 80%+ threshold maintained

- [ ] **No Hand-Written Mocks**
  - Grep: `grep -r "const mock" web-ui/src/__tests__/`
  - Should find only comments, not assignments

---

## Related Documentation

- **AGENTS.md**: Mock best practices and testing patterns
- **CONTRIBUTING.md**: Testing strategy overview
- **fixtures/README.md**: Golden fixtures schema and usage
- **web-ui/src/test-utils/factories.ts**: Mock factory implementations
- **server/tests/integration/test_api_contracts.py**: Integration test examples

---

## Quick Command Reference

```bash
# Backend tests
cd server && uv run pytest

# Frontend tests
cd web-ui && npm test

# Coverage reports
cd server && uv run pytest --cov=app
cd web-ui && npm run test:coverage

# Verify coverage threshold
cd server && uv run coverage report --fail-under=80

# Type checking
cd web-ui && npm run type-check
cd server && PYTHONPATH=. uv run mypy app/ --no-site-packages

# Sync fixtures
./scripts/sync-fixtures.sh

# Full verification before commit
./e2e.test.sh
```
