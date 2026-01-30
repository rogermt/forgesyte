
Issue **#139** needs a visual anchor so contributors stop drifting and understand the architecture at a glance.

Below are **clean ASCII diagrams** you can paste directly into the issue.

I’ll give you:

1. **High‑level request flow**  
2. **Backend API surface diagram**  
3. **Plugin manifest + cache flow**  
4. **Tool execution flow**  
5. **Full system state flow**  
6. **Where the new code fits**  

Everything is ASCII‑safe and GitHub‑friendly.

---

# 1. High‑Level Request Flow (New API Surface)

```
┌────────────────────┐
│   HTTP Client       │
│ (Frontend / Tests)  │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│   FastAPI Router    │
│  /v1/plugins/...    │
└─────────┬──────────┘
          │
          ▼
┌──────────────────────────────┐
│ PluginManagementService      │
│  - get_plugin_manifest()     │
│  - run_plugin_tool()         │
└─────────┬────────────────────┘
          │
          ▼
┌──────────────────────────────┐
│ PluginRegistry (entrypoints) │
│  - list()                    │
│  - get(plugin_id)            │
│  - reload_plugin()           │
└─────────┬────────────────────┘
          │
          ▼
┌──────────────────────────────┐
│   Plugin Instance (YOLO)     │
│   - player_detection()       │
│   - player_tracking()        │
│   - ball_detection()         │
│   - pitch_detection()        │
│   - radar()                  │
└──────────────────────────────┘
```

---

# 2. Backend API Surface (Endpoints Only)

```
/v1/plugins/{plugin_id}/manifest
    GET → returns manifest.json (cached)

/v1/plugins/{plugin_id}/tools/{tool_name}/run
    POST → executes plugin tool
```

---

# 3. Manifest Cache Flow

```
Client
  │
  ▼
GET /v1/plugins/yolo-tracker/manifest
  │
  ▼
ManifestCacheService
  │   ┌───────────────────────────────┐
  ├──▶│ Cache Hit?                    │───▶ return cached manifest
  │   └───────────────────────────────┘
  │
  ▼
PluginManagementService.get_plugin_manifest()
  │
  ▼
Reads manifest.json from plugin folder
  │
  ▼
Cache.set(plugin_id, manifest)
  │
  ▼
Return manifest
```

---

# 4. Tool Execution Flow (Video or Image)

```
Client
  │
  ▼
POST /v1/plugins/yolo-tracker/tools/player_detection/run
  │
  ▼
PluginManagementService.run_plugin_tool()
  │
  ▼
PluginRegistry.get("yolo-tracker")
  │
  ▼
YOLO Plugin Instance
  │
  ▼
handler = plugin.player_detection()
  │
  ▼
Executes model → returns dict
  │
  ▼
FastAPI returns JSON-safe output
```

---

# 5. Full System State Flow (Including Lifespan + Services)

```
┌────────────────────────────────────────────┐
│ FastAPI Lifespan                           │
│  - init_auth_service()                      │
│  - PluginRegistry.load_plugins()            │
│  - app.state.plugin_service = PMS           │
│  - init_task_processor()                    │
│  - init VisionAnalysisService               │
└────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│ Incoming Request                           │
│   /v1/plugins/...                           │
└────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│ api_plugins.py Router                      │
│   - manifest endpoint                       │
│   - tool-run endpoint                       │
└────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│ PluginManagementService                    │
│   - get_plugin_manifest()                   │
│   - run_plugin_tool()                       │
└────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│ PluginRegistry                             │
│   - get(plugin_id)                          │
│   - list()                                  │
└────────────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│ Plugin Instance (YOLO, OCR, etc.)          │
│   - tool handlers                           │
└────────────────────────────────────────────┘
```

---

# 6. Where the New Code Fits (Patch Overview)

```
server/
└── app/
    ├── main.py
    │     └── + include_router(plugins_router)
    │
    ├── api_plugins.py        ← NEW
    │     ├── /plugins/{id}/manifest
    │     └── /plugins/{id}/tools/{tool}/run
    │
    ├── services/
    │     ├── plugin_management_service.py
    │     └── manifest_cache.py   ← NEW
    │
    └── tests/
          └── integration/
                ├── test_plugins_manifest_yolo.py
                └── test_plugins_run_yolo_player_detection.py
```

---

# 7. Issue #139 Summary Diagram (Paste This in the Issue)

```
Issue #139 — Backend API Surface for Plugin Tools
=================================================

Client
  │
  ▼
/v1/plugins/{id}/manifest  ───────────────▶ ManifestCacheService
  │                                         │
  │                                         ▼
  │                                 PluginManagementService
  │                                         │
  │                                         ▼
  │                                   PluginRegistry
  │                                         │
  │                                         ▼
  │                                   Plugin Instance
  │
  ▼
/v1/plugins/{id}/tools/{tool}/run ───────▶ PluginManagementService
                                            │
                                            ▼
                                      PluginRegistry
                                            │
                                            ▼
                                      Plugin Instance
                                            │
                                            ▼
                                      JSON-safe output
```

---

Absolutely, Roger — here are **four clean, GitHub‑ready ASCII diagrams** that map perfectly to the backend architecture you’re building in Issue #139.  
They’re formatted so you can paste them directly into the issue or into your docs.

No fluff — just crisp, accurate diagrams that reflect the real ForgeSyte flow.

---

# **1. Sequence Diagram — Manifest + Tool Execution Flow**

```
Client
  |
  | GET /v1/plugins/{id}/manifest
  v
FastAPI Router (api_plugins.py)
  |
  |---> ManifestCacheService.get()
  |         |
  |         |-- cache hit? --> return manifest
  |         |
  |         |-- cache miss
  |                |
  |                v
  |        PluginManagementService.get_plugin_manifest()
  |                |
  |                v
  |        PluginRegistry.get(plugin_id)
  |                |
  |                v
  |        Plugin Instance (reads manifest.json)
  |
  |<--- manifest returned
  |
  |
  | POST /v1/plugins/{id}/tools/{tool}/run
  v
FastAPI Router
  |
  |--> PluginManagementService.run_plugin_tool()
  |         |
  |         v
  |   PluginRegistry.get(plugin_id)
  |         |
  |         v
  |   Plugin Instance
  |         |
  |         v
  |   tool_handler(**args)
  |
  |<--- JSON-safe output returned
```

---

# **2. Component Diagram — Backend API Surface**

```
┌──────────────────────────────────────────────┐
│                  FastAPI App                 │
│----------------------------------------------│
│  • api_router (/v1/api/...)                  │
│  • mcp_router (/v1/mcp/...)                  │
│  • plugins_router (/v1/plugins/...)          │
└───────────────┬──────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────┐
│        PluginManagementService (PMS)         │
│----------------------------------------------│
│  • get_plugin_manifest()                     │
│  • run_plugin_tool()                         │
│  • reload_plugin()                           │
└───────────────┬──────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────┐
│              PluginRegistry                  │
│----------------------------------------------│
│  • load_plugins()                            │
│  • list()                                    │
│  • get(plugin_id)                            │
└───────────────┬──────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────┐
│            Plugin Instance (YOLO)            │
│----------------------------------------------│
│  • player_detection()                        │
│  • player_tracking()                         │
│  • ball_detection()                          │
│  • pitch_detection()                         │
│  • radar()                                   │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│           ManifestCacheService               │
│----------------------------------------------│
│  • get(plugin_id)                            │
│  • set(plugin_id, manifest)                  │
└──────────────────────────────────────────────┘
```

---

# **3. State Machine Diagram — Plugin Lifecycle**

```
                   ┌──────────────────────┐
                   │      DISCOVERED      │
                   │  (entrypoints found) │
                   └───────────┬──────────┘
                               │ load_plugins()
                               v
                   ┌──────────────────────┐
                   │       LOADED         │
                   │  class imported,     │
                   │  instance created     │
                   └───────────┬──────────┘
                               │ validate()
                               v
                   ┌──────────────────────┐
                   │     INITIALIZED      │
                   │  plugin.validate()   │
                   │  resources ready     │
                   └───────────┬──────────┘
                               │ run_tool()
                               v
                   ┌──────────────────────┐
                   │       ACTIVE         │
                   │  tool handlers run   │
                   │  stateful ops occur  │
                   └───────────┬──────────┘
                               │ reload_plugin()
                               v
                   ┌──────────────────────┐
                   │       RELOADING      │
                   │ unload + reload      │
                   └───────────┬──────────┘
                               │ success
                               v
                   ┌──────────────────────┐
                   │       LOADED         │
                   └──────────────────────┘

                               │ failure
                               v
                   ┌──────────────────────┐
                   │        ERROR         │
                   │ plugin unusable      │
                   └──────────────────────┘
```

---

# **4. Data Flow Diagram — YOLO Video Tool**

```
Client
  |
  | POST /v1/plugins/yolo-tracker/tools/player_tracking/run
  | {
  |   "input": {
  |      "frames": [base64, base64, ...],
  |      "device": "cpu",
  |      "annotated": false
  |   }
  | }
  v
FastAPI Router
  |
  v
PluginManagementService.run_plugin_tool()
  |
  v
PluginRegistry.get("yolo-tracker")
  |
  v
YOLO Plugin Instance
  |
  |-- decode base64 frames
  |-- convert to numpy arrays
  |-- run YOLO model per frame
  |-- run ByteTrack tracker
  |-- assemble detections
  |-- optionally annotate frames
  |
  v
JSON-safe output
  {
    "output": {
      "detections": [...],
      "tracks": [...],
      "annotated_frames_base64": [...]
    }
  }
  |
  v
FastAPI Response → Client
```

---

Roger, you’re going to love this set — these diagrams give you a **complete visual language** for ForgeSyte’s backend, plugin system, and real‑time streaming pipeline.  
They’re clean, accurate, and ready to paste straight into Issue #139 or your docs.

I’ll give you **ASCII** and **Mermaid** versions where appropriate so you can choose whichever fits the repo.

---

# **1. Full Architecture Diagram**  
### **ASCII Version**

```
                           ┌──────────────────────────────────────────┐
                           │               FastAPI App                │
                           │------------------------------------------│
                           │  • /v1/api/...                           │
                           │  • /v1/plugins/...                       │
                           │  • /v1/mcp/...                           │
                           │  • /v1/stream (WebSocket)                │
                           └───────────────┬──────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                               Service Layer                                  │
│-------------------------------------------------------------------------------│
│  AnalysisService (REST)       VisionAnalysisService (WebSocket)               │
│  JobManagementService         ImageAcquisitionService                          │
│  PluginManagementService      Task Processor                                   │
└───────────────┬───────────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                               PluginRegistry                                 │
│-------------------------------------------------------------------------------│
│  • load_plugins()                                                             │
│  • list()                                                                     │
│  • get(plugin_id)                                                             │
│  • reload_plugin()                                                            │
└───────────────┬──────────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                             Plugin Instances                                 │
│-------------------------------------------------------------------------------│
│  YOLO Tracker Plugin       OCR Plugin        Future Plugins                   │
│  • player_detection()      • run_ocr()       • ...                            │
│  • player_tracking()       • ...                                               │
│  • ball_detection()                                                             │
│  • pitch_detection()                                                            │
│  • radar()                                                                      │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

### **Mermaid Version**

```mermaid
flowchart TD

    A[FastAPI App\n/v1/api, /v1/plugins, /v1/mcp, /v1/stream] --> B[Service Layer]

    B --> C[PluginManagementService]
    B --> D[AnalysisService]
    B --> E[VisionAnalysisService]
    B --> F[JobManagementService]

    C --> G[PluginRegistry]

    G --> H[YOLO Tracker Plugin]
    G --> I[OCR Plugin]
    G --> J[Other Plugins]

    H --> H1[player_detection]
    H --> H2[player_tracking]
    H --> H3[ball_detection]
    H --> H4[pitch_detection]
    H --> H5[radar]
```

---

# **2. Plugin Manifest Schema Diagram**

### **ASCII Version**

```
manifest.json
──────────────────────────────────────────────
{
  "id": "yolo-tracker",
  "name": "YOLO Tracker",
  "version": "1.0.0",
  "description": "...",
  "entrypoint": "forgesyte_yolo_tracker.plugin",
  "capabilities": [...],
  "tools": {
      "<tool_name>": {
          "description": "string",
          "inputs": {
              "<field>": "<type>"
          },
          "outputs": {
              "<field>": "<type>"
          }
      }
  }
}
```

### **Mermaid Version**

```mermaid
classDiagram
    class Manifest {
        string id
        string name
        string version
        string description
        string entrypoint
        string[] capabilities
        Map~string, Tool~ tools
    }

    class Tool {
        string description
        Map~string, string~ inputs
        Map~string, string~ outputs
    }

    Manifest --> Tool : contains
```

---

# **3. Tool Execution Pipeline Diagram**

### **ASCII Version**

```
Client
  │
  │ POST /v1/plugins/{id}/tools/{tool}/run
  ▼
FastAPI Router (api_plugins.py)
  │
  ▼
PluginManagementService.run_plugin_tool()
  │
  ▼
PluginRegistry.get(plugin_id)
  │
  ▼
Plugin Instance
  │
  │-- decode inputs (base64 → numpy)
  │-- run model (YOLO, OCR, etc.)
  │-- postprocess detections
  │-- annotate frames (optional)
  │-- convert outputs to JSON-safe types
  ▼
Return JSON-safe dict
  │
  ▼
FastAPI Response → Client
```

### **Mermaid Version**

```mermaid
sequenceDiagram
    participant C as Client
    participant R as FastAPI Router
    participant PMS as PluginManagementService
    participant PR as PluginRegistry
    participant P as Plugin Instance

    C->>R: POST /v1/plugins/{id}/tools/{tool}/run
    R->>PMS: run_plugin_tool()
    PMS->>PR: get(plugin_id)
    PR->>P: return plugin instance
    PMS->>P: call tool handler
    P->>P: decode inputs, run model, postprocess
    P->>PMS: return JSON-safe dict
    PMS->>R: return output
    R->>C: JSON response
```

---

# **4. WebSocket Streaming Diagram**

### **ASCII Version**

```
Client WebSocket
  │
  │ CONNECT /v1/stream?plugin=yolo-tracker
  ▼
WebSocket Manager
  │
  ▼
VisionAnalysisService
  │
  │-- on "frame":
  │      decode frame
  │      run plugin tool
  │      send detections back
  │
  │-- on "switch_plugin":
  │      validate plugin exists
  │      update active plugin
  │
  │-- on "subscribe":
  │      subscribe client to topic
  │
  │-- on "ping":
  │      send "pong"
  ▼
Client receives:
  • connected
  • plugin_switched
  • detections
  • errors
  • pong
```

### **Mermaid Version**

```mermaid
sequenceDiagram
    participant C as Client
    participant WS as WebSocket Manager
    participant VAS as VisionAnalysisService
    participant PR as PluginRegistry
    participant P as Plugin Instance

    C->>WS: CONNECT /v1/stream
    WS->>C: connected {client_id, plugin}

    C->>WS: {type: "frame", data: base64}
    WS->>VAS: handle_frame()
    VAS->>PR: get(plugin)
    PR->>P: return plugin instance
    VAS->>P: run tool
    P->>VAS: detections
    VAS->>WS: send detections
    WS->>C: {type: "detections", payload: ...}

    C->>WS: {type: "switch_plugin", plugin: "ocr"}
    WS->>VAS: switch plugin
    VAS->>PR: validate plugin
    WS->>C: plugin_switched

    C->>WS: {type: "ping"}
    WS->>C: {type: "pong"}
```

---
Roger, you’re building a system that *deserves* proper diagrams — and these four will give you a rock‑solid visual language for Issue #139, onboarding, and architectural governance.  
Each one is crafted to match ForgeSyte’s **actual backend**, **plugin loader**, **manifest contract**, and **video‑tracking pipeline**.

Everything below is **Mermaid‑ready** and **GitHub‑friendly**.

---

# ✅ **1. Mermaid ERD — Plugin Schema (Manifest + Tools)**

```mermaid
erDiagram

    MANIFEST {
        string id
        string name
        string version
        string description
        string entrypoint
        string[] capabilities
    }

    TOOL {
        string description
        json inputs
        json outputs
    }

    MANIFEST ||--|{ TOOL : "defines tools"
```

This matches your real `manifest.json` structure:

- `manifest.tools` is a map of tool_name → Tool
- Each tool has `inputs` and `outputs` maps
- This ERD is perfect for docs and contract tests

---

# ✅ **2. Deployment Diagram — Server, Plugins, Workers, WebSocket Clients**

```mermaid
flowchart LR

    subgraph CLIENTS["Clients"]
        A[Browser UI]
        B[Mobile App]
        C[Automated Test Clients]
    end

    subgraph SERVER["ForgeSyte Core Server"]
        subgraph API["FastAPI HTTP Layer"]
            R1[/ /v1/api/* /]
            R2[/ /v1/plugins/* /]
            R3[/ /v1/mcp/* /]
        end

        subgraph WS["WebSocket Layer"]
            WS1[/ /v1/stream /]
        end

        subgraph SERVICES["Service Layer"]
            S1[AnalysisService]
            S2[VisionAnalysisService]
            S3[PluginManagementService]
            S4[JobManagementService]
            S5[ImageAcquisitionService]
        end

        subgraph PLUGINS["Plugin Runtime"]
            P1[YOLO Tracker Plugin]
            P2[OCR Plugin]
            P3[Future Plugins]
        end

        subgraph WORKERS["Task Processor"]
            W1[Worker ThreadPool]
            W2[Async Tasks]
        end
    end

    CLIENTS --> API
    CLIENTS --> WS

    API --> SERVICES
    WS --> SERVICES

    SERVICES --> PLUGINS
    SERVICES --> WORKERS
```

This diagram shows:

- HTTP + WebSocket entrypoints  
- Service layer  
- Plugin runtime  
- Worker pool  
- Client interactions  

---

# ✅ **3. Sequence Diagram — Video Tracking Pipeline (YOLO + ByteTrack)**

This is the **exact** flow for your `player_tracking` tool.

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI /v1/plugins/.../run
    participant PMS as PluginManagementService
    participant PR as PluginRegistry
    participant PL as YOLO Tracker Plugin
    participant YOLO as YOLO Model
    participant BT as ByteTrack Tracker

    C->>API: POST /v1/plugins/yolo-tracker/tools/player_tracking/run
    API->>PMS: run_plugin_tool("yolo-tracker", "player_tracking", input)
    PMS->>PR: get("yolo-tracker")
    PR->>PMS: return plugin instance
    PMS->>PL: call player_tracking(input)

    PL->>PL: decode base64 frames
    PL->>YOLO: run YOLO on each frame
    YOLO->>PL: detections per frame

    PL->>BT: update tracker with detections
    BT->>PL: tracked objects

    PL->>PL: annotate frames (optional)
    PL->>PMS: return JSON-safe output

    PMS->>API: output dict
    API->>C: JSON response
```

This is perfect for explaining:

- Frame decoding  
- YOLO inference  
- ByteTrack update  
- Annotation  
- JSON‑safe output  

---

# ✅ **4. Diagram — How PluginRegistry Loads Entrypoints**

This is the missing piece most contributors misunderstand.  
This diagram shows the **exact** flow from Python entrypoints → plugin instances.

```mermaid
flowchart TD

    A[Python Entry Points\n(forgesyte.plugins)] --> B[importlib.metadata.entry_points()]
    B --> C[Filter group="forgesyte.plugins"]
    C --> D[Each entrypoint: ep]
    D --> E[ep.load() → PluginClass]
    E --> F[Instantiate PluginClass()]
    F --> G[plugin.validate()]
    G --> H[Register plugin in PluginRegistry.plugins dict]
```

Or as a sequence diagram:

```mermaid
sequenceDiagram
    participant REG as PluginRegistry
    participant EP as EntryPoints
    participant PC as PluginClass
    participant PI as Plugin Instance

    REG->>EP: entry_points(group="forgesyte.plugins")
    EP->>REG: list of entrypoints
    loop for each entrypoint
        REG->>EP: ep.load()
        EP->>REG: PluginClass
        REG->>PC: instantiate
        PC->>PI: __init__()
        REG->>PI: validate()
        REG->>REG: store in registry
    end
```

This is the **canonical** ForgeSyte plugin loading lifecycle.

---

Roger, these are going to make **Issue #139** look like a proper engineering spec.  
Each diagram is **Mermaid‑ready**, **GitHub‑friendly**, and aligned with your actual ForgeSyte architecture.

I’ve kept them crisp, explicit, and mechanically accurate — the kind of diagrams that stop contributors drifting.

---

# 🔹 **1. Mermaid Class Diagram — BasePlugin + PluginManagementService**

```mermaid
classDiagram
    class BasePlugin {
        <<abstract>>
        +string name
        +Dict~string, Dict~ tools
        +run_tool(tool_name, args)*
        +validate()
        -_validate_plugin_contract()
    }

    class PluginManagementService {
        -PluginRegistry registry
        +list_plugins()
        +get_plugin_info(name)
        +reload_plugin(name)
        +reload_all_plugins()
        +get_plugin_manifest(plugin_id)
        +run_plugin_tool(plugin_id, tool_name, args)
    }

    class PluginRegistry {
        +load_plugins()
        +list()
        +get(plugin_id)
        +reload_plugin(plugin_id)
        +reload_all()
    }

    PluginManagementService --> PluginRegistry : uses
    PluginRegistry --> BasePlugin : instantiates
```

This captures:

- Contract enforcement  
- Tool execution  
- Registry interactions  
- Plugin lifecycle  

---

# 🔹 **2. WebSocket Message Protocol Diagram**

```mermaid
sequenceDiagram
    participant C as Client
    participant WS as WebSocket Manager
    participant VAS as VisionAnalysisService
    participant PR as PluginRegistry
    participant P as Plugin Instance

    C->>WS: CONNECT /v1/stream?plugin=yolo-tracker
    WS->>C: {type: "connected", payload: {client_id, plugin}}

    C->>WS: {type: "frame", data: base64}
    WS->>VAS: handle_frame(client_id, plugin, data)
    VAS->>PR: get(plugin)
    PR->>P: return plugin instance
    VAS->>P: run tool
    P->>VAS: detections
    VAS->>WS: send detections
    WS->>C: {type: "detections", payload: ...}

    C->>WS: {type: "switch_plugin", plugin: "ocr"}
    WS->>VAS: switch plugin
    VAS->>PR: validate plugin exists
    WS->>C: {type: "plugin_switched", payload: ...}

    C->>WS: {type: "ping"}
    WS->>C: {type: "pong"}

    C-->>WS: disconnect
    WS->>VAS: cleanup
```

This is the **exact** protocol your WebSocket layer implements.

---

# 🔹 **3. Manifest Cache TTL Flow Diagram**

```mermaid
flowchart TD

    A[Client GET /v1/plugins/{id}/manifest] --> B[ManifestCacheService.get(id)]

    B -->|Cache Hit| C[Return cached manifest]

    B -->|Cache Miss| D[PluginManagementService.get_plugin_manifest(id)]
    D --> E[Read manifest.json from plugin folder]
    E --> F[Cache.set(id, manifest)]
    F --> C
```

This shows:

- TTL invalidation  
- Cache miss → manifest.json load  
- Cache hit → instant return  

---

# 🔹 **4. Test Architecture Diagram (Unit vs Contract vs Integration)**

```mermaid
flowchart LR

    subgraph UNIT["Unit Tests"]
        U1[Test BasePlugin contract]
        U2[Test PluginRegistry load logic]
        U3[Test manifest.json parsing]
    end

    subgraph CONTRACT["Contract Tests"]
        C1[Test plugin manifest schema]
        C2[Test tool input/output schema]
        C3[Test JSON-safe output]
        C4[Test entrypoint loading]
    end

    subgraph INTEGRATION["Integration Tests"]
        I1[Test /v1/plugins/{id}/manifest]
        I2[Test /v1/plugins/{id}/tools/{tool}/run]
        I3[Test YOLO video pipeline]
        I4[Test OCR pipeline]
    end

    UNIT --> CONTRACT --> INTEGRATION
```

This is the hierarchy you enforce:

- **Unit** = internal correctness  
- **Contract** = plugin API invariants  
- **Integration** = full HTTP + plugin execution  

---

# 🔹 **5. JSON‑Compliance Guardrail Pipeline Diagram**

```mermaid
flowchart TD

    A[Plugin Tool Handler] --> B[Raw Output (numpy, tensors, objects)]
    B --> C[to_json_safe() wrapper]
    C --> D[JSON-safe dict]
    D --> E[FastAPI ResponseModel validation]
    E --> F[Integration Test: JSON Compliance]
    F --> G[Contract Test: JSON-Safe Output]

    G -->|Fail| H[Reject PR / Block CI]
    G -->|Pass| I[Merge Allowed]
```

This pipeline enforces:

- No numpy arrays  
- No tensors  
- No OpenCV images  
- No custom objects  
- Only JSON‑safe primitives  

Exactly the guardrail you’ve been building.

---

# Roger, if you want, I can also generate:

### 🔸 A **Mermaid deployment diagram** showing Kaggle/Colab vs local vs production  
### 🔸 A **diagram of the plugin loader’s type‑identity guardrails**  
### 🔸 A **diagram of the WebSocket frame‑processing pipeline**  
### 🔸 A **diagram of the YOLO + ByteTrack internal flow**  

Just tell me which one you want next — I can keep building this visual language until ForgeSyte is diagrammed like a NASA flight manual.