Absolutely, Roger — here is the **complete Phase 14 configuration system**, all in one place, clean, production‑ready, and aligned with the governance style you’ve been enforcing across the project.

This gives you:

- **Full `settings.py` / `config.py` system**  
- **Backend + frontend `.env` templates**  
- **A CORS diagnostic endpoint**  
- **A Phase 14 environment sanity‑check script**  

Everything is deterministic, explicit, and future‑proof.

Let’s build this properly.

---

# ⭐ 1. Phase 14 `settings.py` / `config.py` System  
This is the canonical configuration layer for the backend.

Create:

```
server/app/settings.py
```

```python
import os
from functools import lru_cache
from typing import List


class Settings:
    # -----------------------------
    # Core API configuration
    # -----------------------------
    api_prefix: str = "/v1"

    # -----------------------------
    # CORS configuration
    # -----------------------------
    cors_origins_raw: str = os.getenv("FORGESYTE_CORS_ORIGINS", "")
    cors_origins: List[str] = []

    # -----------------------------
    # Logging configuration
    # -----------------------------
    log_level: str = os.getenv("FORGESYTE_LOG_LEVEL", "INFO")
    log_file: str = os.getenv("FORGESYTE_LOG_FILE", "forgesyte.log")

    # -----------------------------
    # WebSocket configuration
    # -----------------------------
    ws_enabled: bool = os.getenv("FORGESYTE_WS_ENABLED", "true").lower() == "true"

    def __init__(self):
        if self.cors_origins_raw:
            self.cors_origins = [
                origin.strip()
                for origin in self.cors_origins_raw.split(",")
                if origin.strip()
            ]
        else:
            # Safe defaults for local dev
            self.cors_origins = [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

---

# ⭐ 2. Integrate settings into `main.py`

Modify:

```
server/app/main.py
```

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .settings import get_settings

settings = get_settings()

app = FastAPI()

# -----------------------------
# CORS Middleware
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Diagnostic endpoint
# -----------------------------
@app.get("/v1/debug/cors")
def debug_cors():
    return {
        "allowed_origins": settings.cors_origins,
        "raw_env": settings.cors_origins_raw,
    }
```

This gives you a **live endpoint** to confirm CORS config.

---

# ⭐ 3. Backend `.env` Template (Phase 14)

Create:

```
server/.env
```

```env
# -----------------------------
# Backend API configuration
# -----------------------------
FORGESYTE_LOG_LEVEL=INFO
FORGESYTE_LOG_FILE=/kaggle/working/forgesyte/server/forgesyte.log

# -----------------------------
# CORS configuration
# -----------------------------
# Add all allowed frontend origins here
FORGESYTE_CORS_ORIGINS=http://localhost:3000,https://forgetunnel.loca.lt

# -----------------------------
# WebSocket configuration
# -----------------------------
FORGESYTE_WS_ENABLED=true
```

This is the **canonical** way to configure CORS for tunnels, local dev, or production.

---

# ⭐ 4. Frontend `.env` Template (Phase 14)

Create:

```
web-ui/.env.local
```

```env
# REST API base URL
VITE_API_URL=https://forgetunnel.loca.lt/v1

# WebSocket URL
VITE_WS_URL=wss://forgetunnel.loca.lt/v1/stream
```

This ensures:

- REST → correct backend  
- WS → correct backend  
- No more localhost mismatches  

---

# ⭐ 5. CORS Diagnostic Endpoint (already added above)

You now have:

```
GET /v1/debug/cors
```

Example output:

```json
{
  "allowed_origins": [
    "http://localhost:3000",
    "https://forgetunnel.loca.lt"
  ],
  "raw_env": "http://localhost:3000,https://forgetunnel.loca.lt"
}
```

This is invaluable for debugging tunnels.

---

# ⭐ 6. Phase 14 Environment Sanity‑Check Script  
This script verifies:

- REST connectivity  
- WS connectivity  
- CORS headers  
- API prefix correctness  
- Plugin listing endpoint  

Create:

```
scripts/env_check.py
```

```python
import asyncio
import json
import websockets
import requests

API_URL = "https://forgetunnel.loca.lt/v1"
WS_URL = "wss://forgetunnel.loca.lt/v1/stream"


def check_rest():
    print("🔍 Checking REST API:", API_URL)

    try:
        r = requests.options(f"{API_URL}/plugins")
        print("OPTIONS /plugins:", r.status_code)
        print("CORS headers:", r.headers.get("Access-Control-Allow-Origin"))

        r = requests.get(f"{API_URL}/plugins")
        print("GET /plugins:", r.status_code)
        print("Response:", r.json())
    except Exception as e:
        print("❌ REST check failed:", e)


async def check_ws():
    print("\n🔍 Checking WebSocket:", WS_URL)

    try:
        async with websockets.connect(WS_URL) as ws:
            await ws.send(json.dumps({"type": "ping"}))
            msg = await ws.recv()
            print("WS response:", msg)
    except Exception as e:
        print("❌ WS check failed:", e)


if __name__ == "__main__":
    check_rest()
    asyncio.run(check_ws())
```

Run it with:

```
python scripts/env_check.py
```

This gives you a **single command** to verify:

- CORS  
- REST  
- WS  
- Plugin endpoint  
- Tunnel connectivity  

---

# ⭐ 7. Summary

You now have:

### ✔ Full Phase 14 `settings.py` / `config.py`  
### ✔ Backend `.env` template  
### ✔ Frontend `.env.local` template  
### ✔ CORS diagnostic endpoint  
### ✔ Environment sanity‑check script  

This is the **canonical Phase 14 configuration system** — explicit, deterministic, and ready for tunnels, local dev, and production.

---

Roger, here you go — the **full Phase 14 governance pack** you asked for.  
This is the kind of material you’d drop straight into `docs/` and treat as canonical.  
It’s crisp, enforceable, and aligned with the deterministic, governance‑driven engineering culture you’ve been building.

I’ll give you:

1. **Phase 14 Config Governance Doc**  
2. **Phase 14 Deployment Checklist**  
3. **Phase 14 Plugin Metadata Validator (CI‑ready)**  

All in one place, clean and authoritative.

---

# **📘 Phase 14 Configuration Governance Document**  
`docs/governance/phase_14_config_governance.md`

---

## **1. Purpose**

Phase 14 introduces cross‑plugin DAG pipelines, remote tunnels, WebSockets, and multi‑origin UI environments.  
This requires a **formal configuration governance model** to ensure:

- deterministic behavior  
- reproducible environments  
- explicit configuration boundaries  
- safe cross‑origin communication  
- predictable plugin and pipeline loading  

This document defines the **canonical configuration system** for the backend and frontend.

---

## **2. Configuration Principles**

### **2.1 Explicit > Implicit**
No configuration is inferred.  
All environment‑dependent behavior must be explicitly declared.

### **2.2 Deterministic Startup**
The backend must behave identically across:

- local dev  
- tunnels  
- staging  
- production  

### **2.3 Single Source of Truth**
All configuration values must originate from:

```
server/app/settings.py
```

No scattered environment reads.

### **2.4 Safe Defaults**
If a value is missing:

- local dev defaults apply  
- never silently degrade security  
- never silently disable features  

### **2.5 Observability of Configuration**
The system must expose:

```
/v1/debug/cors
/v1/debug/config
```

for runtime introspection.

---

## **3. Configuration Structure**

### **3.1 Backend**

```
server/app/settings.py
server/.env
```

### **3.2 Frontend**

```
web-ui/.env.local
```

### **3.3 Required Environment Variables**

| Variable | Purpose | Required | Example |
|---------|----------|----------|---------|
| `FORGESYTE_CORS_ORIGINS` | Allowed UI origins | Yes | `http://localhost:3000,https://forgetunnel.loca.lt` |
| `FORGESYTE_LOG_LEVEL` | Logging level | No | `INFO` |
| `FORGESYTE_LOG_FILE` | Log file path | No | `/kaggle/.../forgesyte.log` |
| `FORGESYTE_WS_ENABLED` | Enable WebSockets | No | `true` |

### **3.4 Frontend Variables**

| Variable | Purpose | Example |
|---------|----------|---------|
| `VITE_API_URL` | REST base URL | `https://forgetunnel.loca.lt/v1` |
| `VITE_WS_URL` | WebSocket URL | `wss://forgetunnel.loca.lt/v1/stream` |

---

## **4. CORS Governance**

### **4.1 Allowed Origins Must Be Explicit**
Wildcards like `https://*.loca.lt` are **not allowed**.

### **4.2 Tunnel Domains Must Be Listed**
Every tunnel domain must be explicitly added to:

```
FORGESYTE_CORS_ORIGINS
```

### **4.3 CORS Must Be Validated at Runtime**
The endpoint:

```
GET /v1/debug/cors
```

must always reflect the active configuration.

---

## **5. WebSocket Governance**

### **5.1 WS and REST Must Use the Same Origin Set**
If REST allows an origin, WS handshake must allow it too.

### **5.2 WS Must Be Explicitly Enabled**
`FORGESYTE_WS_ENABLED=false` must disable WS endpoints cleanly.

---

## **6. Plugin & Pipeline Governance**

### **6.1 Plugin Metadata Must Be Validated at Startup**
Every plugin must declare:

- `input_types`
- `output_types`
- `capabilities`

### **6.2 Pipeline Definitions Must Be Validated**
Validation includes:

- acyclic graph  
- known plugins  
- known tools  
- type compatibility  

---

## **7. Configuration Drift Prevention**

- All config values must be logged at startup.  
- CI must validate plugin metadata.  
- CI must validate pipeline definitions.  
- CI must validate `.env` templates.  

---

# **📦 Phase 14 Deployment Checklist**  
`docs/deployment/phase_14_deployment_checklist.md`

---

## **1. Pre‑Deployment**

### **1.1 Backend Environment**
- [ ] `.env` file exists  
- [ ] `FORGESYTE_CORS_ORIGINS` set  
- [ ] `FORGESYTE_LOG_LEVEL` set  
- [ ] `FORGESYTE_WS_ENABLED` set  
- [ ] `uvicorn` log level configured  

### **1.2 Frontend Environment**
- [ ] `VITE_API_URL` set  
- [ ] `VITE_WS_URL` set  
- [ ] UI builds successfully  

### **1.3 Plugin Validation**
- [ ] All plugin manifests contain metadata  
- [ ] All tools return dict outputs  
- [ ] All tools accept dict payloads  
- [ ] Plugin metadata validator passes  

### **1.4 Pipeline Validation**
- [ ] All pipelines load  
- [ ] All pipelines pass DAG validation  
- [ ] No cycles  
- [ ] All plugin/tool references valid  

---

## **2. Deployment**

### **2.1 Backend**
- [ ] Start FastAPI  
- [ ] Confirm `/v1/debug/cors`  
- [ ] Confirm `/v1/plugins`  
- [ ] Confirm `/v1/pipelines`  

### **2.2 Frontend**
- [ ] Confirm UI loads  
- [ ] Confirm plugin list loads  
- [ ] Confirm pipeline selector loads  

### **2.3 WebSocket**
- [ ] Confirm WS handshake  
- [ ] Confirm WS frame processing  
- [ ] Confirm WS pipeline execution  

---

## **3. Post‑Deployment**

- [ ] Check logs for errors  
- [ ] Check DuckDB ingestion  
- [ ] Run environment sanity script  
- [ ] Validate MP4 upload (Phase 15 readiness)  

---

# **🧪 Phase 14 Plugin Metadata Validator (CI‑Ready)**  
`tools/validate_plugins.py`

---

```python
#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = ROOT / "plugins"

REQUIRED_FIELDS = ["input_types", "output_types", "capabilities"]


def validate_manifest(path: Path):
    with path.open() as f:
        data = json.load(f)

    errors = []

    for tool_name, tool in data.get("tools", {}).items():
        for field in REQUIRED_FIELDS:
            if field not in tool:
                errors.append(f"{path}: tool '{tool_name}' missing '{field}'")

            elif not isinstance(tool[field], list):
                errors.append(f"{path}: tool '{tool_name}' field '{field}' must be a list")

            elif not tool[field]:
                errors.append(f"{path}: tool '{tool_name}' field '{field}' cannot be empty")

    return errors


def main():
    manifests = list(PLUGINS_DIR.glob("*/manifest.json"))
    all_errors = []

    for manifest in manifests:
        all_errors.extend(validate_manifest(manifest))

    if all_errors:
        print("❌ Plugin metadata validation failed:")
        for err in all_errors:
            print(" -", err)
        sys.exit(1)

    print("✅ All plugin manifests valid.")


if __name__ == "__main__":
    main()
```

---

# **🎯 Summary**

You now have:

### ✔ Phase 14 Config Governance Doc  
### ✔ Phase 14 Deployment Checklist  
### ✔ Phase 14 Plugin Metadata Validator (CI‑ready)  

