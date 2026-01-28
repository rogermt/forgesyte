
# **Contributing to ForgeSyte**  
Thank you for contributing to ForgeSyte. This project values clarity, modularity, and reproducibility.  
Contributions that strengthen those qualities are especially welcome.

---

# Development Environment

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

# Branching Strategy

- `main` — stable  
- `develop` — active development  
- `feature/<name>` — new features  

---

# Code Style

### Python
- Use `uvx ruff format` for formatting  
- Use type hints  
- Keep plugin contracts explicit (`BasePlugin`)  
- Prefer small, composable modules  

### React/TypeScript
- Use Prettier  
- Prefer explicit types  
- Keep UI logic thin; push complexity into hooks/utilities  

---

# Testing Strategy

## Running Tests

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

---

# Schema‑Driven Mocking (Web UI)

ForgeSyte uses **schema‑driven mock data** to ensure UI tests always match real API responses.

### Key Principle  
**Never hand‑write mock objects.**  
Use factory functions or golden fixtures.

### Files
- `fixtures/api-responses.json` — Real API response examples  
- `web-ui/src/test-utils/factories.ts` — Type-safe mock generators  
- `scripts/sync-fixtures.sh` — Auto‑updates fixtures from a running server  

### Example

```ts
// Correct
const job = createMockJob({ status: 'done' });

// Incorrect
const job = { id: '123', status: 'processing' };
```

---

# Golden Fixtures

Fixtures in `fixtures/api-responses.json` are the **source of truth** for API response shapes.

Example test:

```python
def test_jobs_endpoint(client):
    response = client.get('/v1/jobs?limit=10')
    expected = FIXTURES['jobs_list']
    assert response.json() == expected
```

---

# Syncing Fixtures

When API endpoints change:

```bash
cd server
uv sync
./scripts/sync-fixtures.sh
```

This script:

1. Starts a local test server  
2. Calls all real API endpoints  
3. Updates `fixtures/api-responses.json`  
4. Validates JSON structure  
5. Creates a backup  

---

# Integration Tests

Integration tests verify that **real plugins** and **real endpoints** behave as documented.

Example:

```python
@pytest.mark.integration
async def test_jobs_endpoint_response_shape(client):
    response = await client.get("/v1/jobs?limit=10")
    data = response.json()

    assert "jobs" in data
    assert "count" in data
    for job in data["jobs"]:
        assert "job_id" in job
        assert job["status"] in ["queued", "running", "done", "error", "not_found"]
```

---

# Checklist for Adding Tests

- [ ] Use mock factories, not hand-written mocks  
- [ ] Field names match API exactly  
- [ ] Enum values match server enums  
- [ ] Integration tests verify API contracts  
- [ ] Update fixtures if API changes  
- [ ] All tests pass (`npm test`, `pytest`)  
- [ ] Coverage ≥ 80%  

---

# Pull Requests

Include:

- What changed  
- Why  
- How to test  
- Any breaking changes  
- Screenshots (if UI)  

---

# Adding Plugins (Updated for BasePlugin)

See `PLUGIN_DEVELOPMENT.md`.

Plugins must:

- Subclass `BasePlugin`  
- Define a unique `name`  
- Define a `tools` dictionary mapping tool names → callables  
- Implement `run_tool(self, tool_name, args)`  
- Optionally implement `validate()` for model loading or environment checks  
- Avoid heavy dependencies unless necessary  
- Provide JSON‑serializable outputs  

### Example Plugin Skeleton

```python
from app.plugins.base import BasePlugin

class Plugin(BasePlugin):
    name = "example-plugin"

    def __init__(self):
        self.tools = {
            "detect": self.detect,
            "classify": self.classify,
        }
        super().__init__()

    def run_tool(self, tool_name, args):
        return self.tools[tool_name](**args)

    def detect(self, image_base64: str):
        ...

    def classify(self, image_base64: str):
        ...
```

### Tool Execution Endpoint

```
POST /v1/plugins/<plugin>/tools/<tool>/run
```

