

---# ⭐ 1. **Backend Patch — Fix `/v1/plugins` returning dicts vs objects**

Your current code:

```python
"plugins": [plugin.metadata() for plugin in plugins]
```

This is **pre‑Phase‑11** and assumes plugin objects with `.metadata()`.

But Phase 11 returns **dicts** from `PluginRegistry.all_status()`.

### ✅ Replace the entire endpoint with:

```python
@router.get("/v1/plugins")
def list_plugins():
    return registry.all_status()
```

Or if you want a wrapper:

```python
@router.get("/v1/plugins")
def list_plugins():
    return {"plugins": registry.all_status()}
```

### Why this works  
- `registry.all_status()` returns a list of dicts  
- Each dict matches `PluginHealthResponse`  
- No `.metadata()` calls  
- No plugin objects leak into API  
- Web‑ui receives stable JSON  

This is the **Phase 11 canonical shape**.

---

# ⭐ 2. **Frontend Patch — Fix plugin list rendering**

Your web‑ui is still doing something like:

```ts
plugin.metadata()
```

or expecting:

```ts
plugin.id
plugin.version
plugin.author
```

But Phase 11 returns:

```json
{
  "name": "videotracker",
  "state": "UNAVAILABLE",
  "description": "Video tracking plugin",
  "reason": "CUDA not found",
  "success_count": 0,
  "error_count": 1,
  "last_used": "...",
  "uptime_seconds": 123
}
```

### ✅ Update the web‑ui to use:

```ts
plugin.name
plugin.state
plugin.description
plugin.reason
plugin.success_count
plugin.error_count
```

### Example React patch:

```tsx
{plugins.map(p => (
  <PluginCard
    key={p.name}
    name={p.name}
    state={p.state}
    description={p.description}
    reason={p.reason}
  />
))}
```

No `.metadata()` anywhere.

---

# ⭐ 3. **Missing Integration Test — Prevents this regression forever**

Create:

```
server/tests/test_plugin_health_api/test_webui_contract.py
```

### Add:

```python
def test_webui_plugin_contract(client):
    resp = client.get("/v1/plugins")
    assert resp.status_code == 200

    body = resp.json()
    assert isinstance(body, list)

    for plugin in body:
        assert isinstance(plugin, dict)
        assert "name" in plugin
        assert "state" in plugin
        assert "description" in plugin
        assert "reason" in plugin
```

### What this test guarantees  
- Backend returns **list of dicts**  
- No plugin objects  
- No `.metadata()`  
- No 500s  
- Web‑ui contract is stable  

This test alone would have caught your error instantly.

---

# ⭐ 4. **Phase 11 API Contract — `/v1/plugins`**

Drop this into `.ampcode/PHASE_11_API_CONTRACT.md`:

```md
# Phase 11 API Contract — /v1/plugins

## Response Shape (Authoritative)

GET /v1/plugins → 200

[
  {
    "name": "string",
    "state": "LOADED | INITIALIZED | RUNNING | FAILED | UNAVAILABLE",
    "description": "string",
    "reason": "string | null",
    "success_count": int,
    "error_count": int,
    "last_used": "ISO timestamp | null",
    "uptime_seconds": int
  }
]

## Rules

- MUST return a list of dicts (not plugin objects)
- MUST NOT call plugin.metadata()
- MUST NOT return 500
- MUST return 200 even if plugins FAILED or UNAVAILABLE
- MUST include all fields above
- MUST be consumed by web-ui as plain JSON
```

This locks the contract permanently.

---

# ⭐ Why your old error happened  
Your backend returned:

```python
[ { ...dict... }, { ...dict... } ]
```

Your web‑ui expected:

```ts
plugin.metadata()
```

FastAPI tried to call `.metadata()` on a dict → **500**.

Phase 11 fixes this by:

- enforcing dict‑only plugin health  
- enforcing stable API contract  
- adding integration tests  
- updating frontend to match backend  

---

# ⭐ Want me to generate the exact diff patches (backend + frontend)?  
I can produce:

- `git diff` style patches  
- File‑by‑file replacements  
- A Phase 11 “Fix Plugin List” PR template  
- A Phase 11 “Web‑UI Contract Enforcement Test” suite  

Just say **“generate patches”**.