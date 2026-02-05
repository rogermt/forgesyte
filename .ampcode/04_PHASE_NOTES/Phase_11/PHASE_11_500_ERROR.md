Nice, this is exactly the kind of explicit QA snapshot that makes Phase 11 real instead of vibes.

The big red flag is here:

> `GET /v1/plugins/{name}/health` → 500 for `http://localhost:8000/v1/plugins/ocr`

That means your **per‑plugin health endpoint** is still violating the Phase 11 rule:  
> “Health API returns 200/404 only, never 500.”

Let’s fix that one surgically.

---

### 1. Patch `/v1/plugins/{name}/health` to never 500

Find your handler, something like:

```python
@router.get("/v1/plugins/{name}/health")
def get_plugin_health(name: str):
    status = registry.get_status(name)
    return status  # or status.dict()
```

The 500 is almost certainly coming from one of:

- `registry` not being the singleton  
- `get_status(name)` returning `None` and you not handling it  
- returning a Pydantic model without `.dict()` in a way FastAPI doesn’t like  
- an exception inside `get_status` (e.g., missing metadata/state)

Use this Phase 11‑compliant version:

```python
from fastapi import HTTPException
from app.plugins.loader.plugin_registry import get_registry

# TEST-CHANGE (Phase 11): Per-plugin health must return 200/404 only

@router.get("/v1/plugins/{name}/health")
def get_plugin_health(name: str):
    registry = get_registry()
    status = registry.get_status(name)

    if status is None:
        # Plugin not known → 404
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")

    # Known plugin → 200 with JSON body
    return status
```

If `status` is a Pydantic model (`PluginHealthResponse`), FastAPI will serialize it correctly.

Now:

- existing plugin → 200  
- unknown plugin → 404  
- no code path throws → no 500

---

### 2. Re‑run just the failing bit

After that patch:

```bash
curl -i http://localhost:8000/v1/plugins/ocr/health
curl -i http://localhost:8000/v1/plugins/does_not_exist/health
```

Expected:

- `ocr/health` → `200` with full health JSON  
- `does_not_exist/health` → `404` with JSON error  
- your “Never returns 500” checkbox becomes ✅

---

### 3. Tiny note on your summary block

At the bottom you’ve got:

```md
- [ ] Plugin Execution Safety: **0/3** ✓
```

Those `0/3` are still placeholders—once you start ticking boxes, update them to real counts (e.g. `2/3`), and drop the ✓ until the whole section is green.

---

If you paste the current `/v1/plugins/{name}/health` handler and the traceback for that 500, I can line‑edit it to the exact final form—but the pattern above is the Phase 11‑correct shape.