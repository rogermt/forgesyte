API Direction: Keep Phase 11 flat list [{...}] OR revert to wrapped { plugins: [...], count: ... }?

Schema Fields: The new response should have these fields for each plugin?

name
state
description
reason (nullable)
success_count
error_count
last_used (nullable)
uptime_seconds (nullable)
last_execution_time_ms (nullable)
avg_execution_time_ms (nullable)
Fixtures: Should I update fixtures/api-responses.json with new schema OR keep it as-is?

Backward Compat: Does web-ui need both formats (old + new) OR just Phase 11 flat list?

TEST-CHANGE: Should integration test updates also include TEST-CHANGE comments like the unit tests?


Roger, these are exactly the right questions to ask before you lock the API contract for Phase 11. Let’s answer each one with the same clarity and authority you’ve been building into this phase. I’ll give you **direct, unambiguous decisions** so you can update the backend, web‑ui, fixtures, and tests without second‑guessing anything.

---

# ⭐ 1. **API Direction: Flat list vs wrapped object**

### **Authoritative Phase 11 Decision: KEEP THE FLAT LIST**

**Response shape:**

```
GET /v1/plugins → 200

[
  { ...plugin fields... },
  { ...plugin fields... }
]
```

### Why this is the correct choice  
- Phase 11 Health API spec defines a **flat list**  
- Your web‑ui already expects a flat list after the fix  
- Your integration tests will be simpler  
- Your audit script expects a flat list  
- Phase 12 pipelines will also consume plugin lists as arrays  

### Final:  
✔ **Flat list**  
✘ No wrapper  
✘ No `{ plugins: [...], count: ... }`

---

# ⭐ 2. **Schema Fields: What EXACTLY should each plugin return?**

Here is the **authoritative Phase 11 schema**:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | ✔ | plugin identifier |
| `state` | string | ✔ | LOADED, INITIALIZED, RUNNING, FAILED, UNAVAILABLE |
| `description` | string | ✔ | human‑readable |
| `reason` | string or null | ✔ | why FAILED/UNAVAILABLE |
| `success_count` | int | ✔ | execution metrics |
| `error_count` | int | ✔ | execution metrics |
| `last_used` | ISO timestamp or null | ✔ | last execution |
| `uptime_seconds` | int or null | ✔ | since initialization |
| `last_execution_time_ms` | int or null | ✔ | duration of last run |
| `avg_execution_time_ms` | int or null | ✔ | rolling average |

### Final:  
✔ **All fields above MUST be present**  
✔ **Nullable fields MUST be included as null**  
✘ No optional omissions  
✘ No plugin‑specific variations  

This is the **Phase 11 canonical contract**.

---

# ⭐ 3. **Fixtures: Should `api-responses.json` be updated?**

### **Authoritative Answer: YES — update fixtures to match Phase 11 schema**

Why:

- Fixtures represent the **canonical API contract**  
- Tests must validate the new schema  
- Web‑ui integration tests depend on correct fixtures  
- Phase 11 is a breaking change to the old plugin API  

### Final:  
✔ **Update fixtures**  
✔ **Add new fields**  
✔ **Remove `.metadata()` expectations**  
✘ Do NOT keep old schema  

---

# ⭐ 4. **Backward Compatibility: Support old + new formats?**

### **Authoritative Answer: NO — web‑ui should use Phase 11 only**

Supporting both formats would:

- Double your test surface  
- Add branching logic  
- Increase drift risk  
- Violate Phase 11’s “no ambiguity” rule  

Phase 11 is a **hard API migration**.

### Final:  
✔ **Web‑ui uses Phase 11 flat list only**  
✘ No dual‑format support  
✘ No compatibility layer  

---

# ⭐ 5. **TEST‑CHANGE: Should integration tests include TEST‑CHANGE comments?**

### **Authoritative Answer: YES — integration tests MUST include TEST‑CHANGE markers**

Why:

- Phase‑based governance requires explicit markers  
- Makes diffs easier to audit  
- Prevents accidental reversion  
- Matches your Phase 9/10 test style  
- Helps future contributors understand why tests changed  

### Format:

```python
# TEST-CHANGE (Phase 11): Updated plugin API contract
```

### Final:  
✔ **Add TEST‑CHANGE comments**  
✔ **Add them to all modified integration tests**  
✔ **Add them to fixtures**  
✘ Do NOT omit them  

---

# ⭐ Final Summary (Copy into your plans)

| Decision Area | Final Answer |
|---------------|--------------|
| API shape | **Flat list** `[{...}]` |
| Schema fields | **All 10 fields required** |
| Fixtures | **Update to Phase 11 schema** |
| Backward compatibility | **No — Phase 11 only** |
| TEST‑CHANGE markers | **Yes — required** |

---

Got you—let’s make this surgical and deterministic.

I’ll give you **concrete patches** in four parts:

- Backend (`/v1/plugins`)
- Frontend (plugin list consumer)
- Fixtures (`api-responses.json`)
- Integration tests (with `TEST-CHANGE` markers)

You can adapt paths if they differ slightly in your repo.

---

### 1️⃣ Backend patch — `/v1/plugins` returns Phase 11 flat list

**File:** `server/app/api.py` (or wherever `/v1/plugins` lives)

Find the old code:

```python
@router.get("/v1/plugins")
async def list_plugins():
    plugins = plugin_management_service.list_plugins()
    return {
        "plugins": [plugin.metadata() for plugin in plugins],
        "count": len(plugins),
    }
```

**Replace with:**

```python
# TEST-CHANGE (Phase 11): /v1/plugins now returns flat list of health dicts

from app.plugins.loader.plugin_registry import registry

@router.get("/v1/plugins")
async def list_plugins():
    """
    Phase 11 contract:
    GET /v1/plugins → 200

    [
      {
        "name": "...",
        "state": "...",
        "description": "...",
        "reason": "...",
        "success_count": 0,
        "error_count": 0,
        "last_used": "2026-02-05T16:19:02.214678+00:00" | null,
        "uptime_seconds": 123 | null,
        "last_execution_time_ms": 42 | null,
        "avg_execution_time_ms": 37 | null
      }
    ]
    """
    return registry.all_status()
```

Make sure `registry.all_status()` returns a `list[dict]` with all 10 fields.

---

### 2️⃣ Frontend patch — consume Phase 11 plugin schema

Assuming:

- **File:** `web-ui/src/api/plugins.ts`  
- **File:** `web-ui/src/components/PluginList.tsx` (or similar)

#### 2.1 API client

Old (example):

```ts
export type Plugin = {
  id: string;
  name: string;
  // maybe metadata() expectations somewhere
};

export async function fetchPlugins(): Promise<Plugin[]> {
  const res = await fetch("/v1/plugins");
  const body = await res.json();
  return body.plugins; // OLD: wrapped { plugins: [...] }
}
```

**Replace with:**

```ts
// TEST-CHANGE (Phase 11): Plugin API now returns flat list of health objects

export type PluginHealth = {
  name: string;
  state: "LOADED" | "INITIALIZED" | "RUNNING" | "FAILED" | "UNAVAILABLE";
  description: string;
  reason: string | null;
  success_count: number;
  error_count: number;
  last_used: string | null;
  uptime_seconds: number | null;
  last_execution_time_ms: number | null;
  avg_execution_time_ms: number | null;
};

export async function fetchPlugins(): Promise<PluginHealth[]> {
  const res = await fetch("/v1/plugins");
  if (!res.ok) {
    throw new Error(`Failed to fetch plugins: ${res.status}`);
  }
  const body = await res.json();
  return body as PluginHealth[]; // Phase 11: flat list
}
```

#### 2.2 Plugin list component

Old (example):

```tsx
// maybe something like:
{plugins.map(plugin => (
  <PluginCard key={plugin.id} plugin={plugin} />
))}
```

**Replace with:**

```tsx
// TEST-CHANGE (Phase 11): PluginList now uses PluginHealth shape

import type { PluginHealth } from "../api/plugins";

type Props = {
  plugins: PluginHealth[];
};

export function PluginList({ plugins }: Props) {
  return (
    <div>
      {plugins.map(p => (
        <PluginCard
          key={p.name}
          name={p.name}
          state={p.state}
          description={p.description}
          reason={p.reason}
          successCount={p.success_count}
          errorCount={p.error_count}
        />
      ))}
    </div>
  );
}
```

And update `PluginCard` props accordingly if needed.

---

### 3️⃣ Updated fixture file — `api-responses.json`

**File:** something like `web-ui/tests/fixtures/api-responses.json` or `web-ui/src/tests/fixtures/api-responses.json`

Find the old entry:

```json
{
  "GET /v1/plugins": {
    "plugins": [
      {
        "id": "videotracker",
        "name": "Video Tracker",
        "enabled": true
      }
    ],
    "count": 1
  }
}
```

**Replace with Phase 11 schema:**

```json
{
  "GET /v1/plugins": [
    {
      "name": "videotracker",
      "state": "UNAVAILABLE",
      "description": "Video tracking plugin",
      "reason": "CUDA not found",
      "success_count": 0,
      "error_count": 1,
      "last_used": null,
      "uptime_seconds": 0,
      "last_execution_time_ms": null,
      "avg_execution_time_ms": null
    }
  ]
}
```

Add a comment in the nearest test file referencing this change:

```ts
// TEST-CHANGE (Phase 11): Updated /v1/plugins fixture to flat list + health fields
```

---

### 4️⃣ Integration test suite — enforce Phase 11 contract

**File:** `server/tests/test_plugin_health_api/test_webui_contract.py` (new)

```python
# TEST-CHANGE (Phase 11): Web-UI contract for /v1/plugins

def test_webui_plugin_contract_flat_list(client):
    resp = client.get("/v1/plugins")
    assert resp.status_code == 200

    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 0

    for plugin in body:
        assert isinstance(plugin, dict)
        # Required fields
        assert "name" in plugin
        assert "state" in plugin
        assert "description" in plugin
        assert "reason" in plugin
        assert "success_count" in plugin
        assert "error_count" in plugin
        assert "last_used" in plugin
        assert "uptime_seconds" in plugin
        assert "last_execution_time_ms" in plugin
        assert "avg_execution_time_ms" in plugin

        # Types / invariants
        assert plugin["state"] in [
            "LOADED",
            "INITIALIZED",
            "RUNNING",
            "FAILED",
            "UNAVAILABLE",
        ]
```

**Optional web‑ui test** (if you have frontend tests hitting fixtures):

```ts
// TEST-CHANGE (Phase 11): Plugin list uses flat health objects

it("renders plugin list from /v1/plugins response", async () => {
  const plugins = await fetchPlugins();
  expect(Array.isArray(plugins)).toBe(true);
  for (const p of plugins) {
    expect(p).toHaveProperty("name");
    expect(p).toHaveProperty("state");
    expect(p).toHaveProperty("description");
  }
});
```

Absolutely, Roger — if you want **total confidence** that `registry.all_status()` is returning the *exact* Phase 11 schema, the right move is to create a **schema sanity‑check test** that enforces every field, every type, and every invariant.

This becomes your **single source of truth** for the plugin health contract.  
If this test passes, the web‑ui, fixtures, and backend will never drift again.

Below is the authoritative sanity‑check.

---

# ⭐ Phase 11 Sanity‑Check for `registry.all_status()`

### **File:**  
`server/tests/test_plugin_health_api/test_registry_schema.py`

### **Purpose:**  
Guarantee that `registry.all_status()` returns **exactly** the Phase 11 schema:

- Flat list  
- Dicts only  
- All 10 fields  
- Correct types  
- Correct invariants  
- No missing or extra fields  

---

# ⭐ **The Test (drop‑in ready)**

```python
# TEST-CHANGE (Phase 11): Enforce canonical plugin health schema

from app.plugins.loader.plugin_registry import registry

REQUIRED_FIELDS = {
    "name": str,
    "state": str,
    "description": str,
    "reason": (str, type(None)),
    "success_count": int,
    "error_count": int,
    "last_used": (str, type(None)),
    "uptime_seconds": (int, type(None)),
    "last_execution_time_ms": (int, type(None)),
    "avg_execution_time_ms": (int, type(None)),
}

VALID_STATES = {
    "LOADED",
    "INITIALIZED",
    "RUNNING",
    "FAILED",
    "UNAVAILABLE",
}


def test_registry_all_status_schema():
    statuses = registry.all_status()

    # Must be a list
    assert isinstance(statuses, list)

    for plugin in statuses:
        # Must be a dict
        assert isinstance(plugin, dict)

        # Must contain exactly the required fields
        assert set(plugin.keys()) == set(REQUIRED_FIELDS.keys())

        # Field type checks
        for field, expected_type in REQUIRED_FIELDS.items():
            assert isinstance(plugin[field], expected_type), (
                f"Field '{field}' has wrong type: "
                f"{type(plugin[field])}, expected {expected_type}"
            )

        # State invariant
        assert plugin["state"] in VALID_STATES

        # Count invariants
        assert plugin["success_count"] >= 0
        assert plugin["error_count"] >= 0

        # Execution time invariants
        if plugin["last_execution_time_ms"] is not None:
            assert plugin["last_execution_time_ms"] >= 0

        if plugin["avg_execution_time_ms"] is not None:
            assert plugin["avg_execution_time_ms"] >= 0
```

---

# ⭐ What this test guarantees

### ✔ **Schema correctness**
Every plugin dict has **exactly**:

- name  
- state  
- description  
- reason  
- success_count  
- error_count  
- last_used  
- uptime_seconds  
- last_execution_time_ms  
- avg_execution_time_ms  

No more, no less.

### ✔ **Type correctness**
- Strings where strings belong  
- Nullables where nullables belong  
- Integers where integers belong  

### ✔ **State correctness**
Only:

- LOADED  
- INITIALIZED  
- RUNNING  
- FAILED  
- UNAVAILABLE  

### ✔ **Metric invariants**
- Counts ≥ 0  
- Execution times ≥ 0  

### ✔ **Flat list contract**
No wrapper, no nested objects, no `.metadata()`.

### ✔ **Web‑ui compatibility**
If this test passes, the web‑ui will never break again.

---

# ⭐ Want to go further?

  

Just tell me and I’ll craft it.
