# 📦 PART 2: v1.0.0 DOCUMENTATION

---

# 📋 1. OVERVIEW — v1.0.0

## **v1.0.0 — First Stable Release (MCP Integration + Stabilization)**

### **Purpose**
v1.0.0 is the **first stable, production-ready release** of the Vision Processing System. This release delivers **MCP (Model Context Protocol) integration** to enable Gemini-CLI extension support, plus **architectural stabilization** and **governance enforcement**.

### **What Came Before**

| Version | Name | Status | Summary |
|---------|------|--------|---------|
| v0.8.0 | Phase 15 | ✅ Stable | Synchronous batch video processing |
| v0.8.1 | Phase 16 | ✅ Stable | Async job system |
| v0.9.0 | Video Upload | ✅ Stable | Video upload to Web UI |

### **What v1.0.0 Delivers**

✅ **MCP Server Implementation**
- MCP-compliant server
- Tool discovery endpoint
- Tool execution endpoint
- Schema definition endpoint

✅ **Gemini-CLI Extension**
- MCP client for Gemini CLI
- Tool discovery
- Image analysis via Gemini
- Video processing via Gemini
- Full integration with backend

✅ **Architecture Stabilization**
- Plugin architecture cleanup
- Pipeline registry cleanup
- Folder structure normalization
- Code pattern enforcement

✅ **Governance Enforcement**
- Naming convention validation
- Folder structure validation
- Forbidden vocabulary prevention
- Contributor guidelines

✅ **Documentation**
- Complete API documentation
- Complete MCP documentation
- Complete governance documentation
- Migration guides

### **What v1.0.0 Does NOT Change**
- ✅ Phase 15 video pipeline unchanged
- ✅ Phase 16 async job system unchanged
- ✅ v0.9.0 video upload unchanged
- ✅ Image analysis unchanged
- ✅ Web UI unchanged (except minor fixes)

### **Key Principle**
> **v1.0.0 = MCP + Stabilization. Production Ready.**

---

# 🏗️ 2. HIGH-LEVEL DESIGN (HLD) — v1.0.0

## **System Architecture (v1.0.0)**

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                            │
├─────────────────────────────────────────────────────────────┤
│  Web UI (v0.9.0)              Gemini-CLI (NEW)               │
│  - Plugin Selector            - MCP Client                   │
│  - Tool Selector              - Tool Discovery               │
│  - Image Upload               - Image Analysis               │
│  - Video Upload               - Video Processing             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       API LAYER                              │
├─────────────────────────────────────────────────────────────┤
│  REST API (Existing)          MCP API (NEW)                  │
│  - /v1/image/analyze          - /mcp/tools                   │
│  - /v1/video/submit           - /mcp/schema                  │
│  - /v1/video/status           - /mcp/execute/{tool}          │
│  - /v1/video/results                                         │
│  - /v1/plugins                                               │
│  - /v1/pipelines                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  BUSINESS LOGIC LAYER                        │
├─────────────────────────────────────────────────────────────┤
│  MCP Server (NEW)             Pipeline Registry (CLEANED)    │
│  - Tool Registry              - Phase 15 Video               │
│  - Schema Generator           - Image Pipelines              │
│  - Tool Executor              - Tool Mapping                 │
│                                                               │
│  Plugin Manager (CLEANED)     Job Manager (Existing)         │
│  - Plugin Discovery           - Job Creation                 │
│  - Manifest Validation        - Status Tracking              │
│  - Type Validation            - Result Storage               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   EXECUTION LAYER (Unchanged)                │
├─────────────────────────────────────────────────────────────┤
│  Worker Process               VideoFilePipelineService       │
│  - Dequeue Jobs               - Frame Extraction             │
│  - Execute Pipelines          - YOLO Detection               │
│  - Save Results               - OCR Processing               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                PERSISTENCE LAYER (Unchanged)                 │
├─────────────────────────────────────────────────────────────┤
│  Database                     Object Storage                 │
│  Queue                                                        │
└─────────────────────────────────────────────────────────────┘
```

## **New Components in v1.0.0**

### **1. MCP Server**
- **Location:** `/mcp/server.py`
- **Responsibilities:**
  - Serve MCP schema
  - Serve tool list
  - Execute tools
  - Map tools to pipelines
  - Map tools to plugins

### **2. Tool Registry**
- **Location:** `/mcp/tool_registry.py`
- **Responsibilities:**
  - Discover available tools
  - Validate tool definitions
  - Map tools to backend pipelines

### **3. Schema Generator**
- **Location:** `/mcp/schema_generator.py`
- **Responsibilities:**
  - Generate MCP schema from tool definitions
  - Validate schema
  - Serve schema via `/mcp/schema`

### **4. Tool Executor**
- **Location:** `/mcp/executor.py`
- **Responsibilities:**
  - Execute tools via plugins
  - Execute tools via pipelines
  - Handle tool parameters
  - Return tool results

### **5. Gemini-CLI MCP Extension**
- **Location:** `/gemini-cli-extension/`
- **Responsibilities:**
  - MCP client implementation
  - Connect to MCP server
  - Discover tools
  - Execute tools from Gemini CLI
  - Display results in Gemini

## **MCP Data Flow**

```
Gemini CLI
  → Gemini-CLI MCP Extension (MCP Client)
    → GET /mcp/tools
      → Tool Registry
        → Returns: [
            { name: "analyze_image", description: "...", parameters: {...} },
            { name: "process_video", description: "...", parameters: {...} }
          ]
    → User selects "analyze_image"
    → POST /mcp/execute/analyze_image
        Body: { image_base64: "...", pipeline_id: "yolo_ocr" }
      → Tool Executor
        → Load pipeline "yolo_ocr"
        → Execute via Plugin Manager
        → Return results
      → Gemini-CLI displays results
```

---

# 📝 3. FUNCTIONAL REQUIREMENTS — v1.0.0

## **FR-1: MCP Server Must Serve Tools**
**Description:** MCP server must expose available tools via `/mcp/tools`.

**Acceptance Criteria:**
- ✅ `/mcp/tools` returns valid tool list
- ✅ Each tool includes name, description, parameters
- ✅ Tool list is discoverable by MCP clients

---

## **FR-2: MCP Server Must Serve Schema**
**Description:** MCP server must expose MCP schema via `/mcp/schema`.

**Acceptance Criteria:**
- ✅ `/mcp/schema` returns valid JSON schema
- ✅ Schema describes all tools
- ✅ Schema validates against MCP spec

---

## **FR-3: MCP Server Must Execute Tools**
**Description:** MCP server must execute tools via `/mcp/execute/{tool}`.

**Acceptance Criteria:**
- ✅ Tool execution works for image analysis
- ✅ Tool execution works for video processing
- ✅ Tool parameters are validated
- ✅ Tool results are returned

---

## **FR-4: Gemini-CLI Extension Must Connect**
**Description:** Gemini-CLI extension must connect to MCP server.

**Acceptance Criteria:**
- ✅ Extension discovers MCP server
- ✅ Extension fetches tool list
- ✅ Extension fetches schema
- ✅ Extension is ready to execute tools

---

## **FR-5: Gemini-CLI Extension Must Execute Tools**
**Description:** Gemini-CLI extension must execute tools from Gemini.

**Acceptance Criteria:**
- ✅ User can analyze images from Gemini
- ✅ User can process videos from Gemini
- ✅ Results are displayed in Gemini
- ✅ Errors are displayed in Gemini

---

## **FR-6: Plugin Architecture Must Be Consistent**
**Description:** All plugins must follow same structure.

**Acceptance Criteria:**
- ✅ All manifests are valid
- ✅ All plugin types are correct
- ✅ All tool definitions are correct
- ✅ All run() signatures are consistent

---

## **FR-7: Pipeline Registry Must Be Clean**
**Description:** Pipeline registry must be rebuilt and validated.

**Acceptance Criteria:**
- ✅ All pipelines load correctly
- ✅ All pipeline configs are valid
- ✅ Tools map correctly to pipelines

---

## **FR-8: Governance Rules Must Be Enforced**
**Description:** CI must validate governance rules.

**Acceptance Criteria:**
- ✅ Folder structure is validated
- ✅ Naming conventions are validated
- ✅ Forbidden vocabulary is prevented
- ✅ All PRs pass governance checks

---

# 📝 4. NON-FUNCTIONAL REQUIREMENTS — v1.0.0

## **NFR-1: Backward Compatibility**
**Description:** v1.0.0 must not break existing functionality.

**Acceptance Criteria:**
- ✅ All Phase 15 tests pass
- ✅ All Phase 16 tests pass
- ✅ All v0.9.0 tests pass
- ✅ Web UI still works
- ✅ REST API still works

---

## **NFR-2: MCP Compliance**
**Description:** MCP implementation must follow MCP spec.

**Acceptance Criteria:**
- ✅ Schema is MCP-compliant
- ✅ Tool definitions are MCP-compliant
- ✅ Tool execution is MCP-compliant

---

## **NFR-3: Performance**
**Description:** v1.0.0 must not degrade performance.

**Acceptance Criteria:**
- ✅ Image analysis latency unchanged
- ✅ Video processing latency unchanged
- ✅ MCP tool execution is fast (<1s overhead)

---

## **NFR-4: Code Quality**
**Description:** Codebase must be clean and maintainable.

**Acceptance Criteria:**
- ✅ No dead code
- ✅ No duplicate code
- ✅ Consistent naming
- ✅ Consistent structure

---

## **NFR-5: Documentation**
**Description:** All features must be documented.

**Acceptance Criteria:**
- ✅ MCP API documented
- ✅ Tool definitions documented
- ✅ Gemini-CLI usage documented
- ✅ Governance rules documented

---

## **NFR-6: Test Coverage**
**Description:** All new functionality must be tested.

**Acceptance Criteria:**
- ✅ MCP server has unit tests
- ✅ MCP server has integration tests
- ✅ Gemini-CLI has integration tests
- ✅ Governance has validation tests

---

# 👤 5. USER STORIES — v1.0.0

## **US-1: Analyze Images via Gemini**
**As a user**  
I want to analyze images using Gemini CLI  
So that I can get YOLO + OCR results without leaving Gemini.

**Acceptance Criteria:**
- ✅ I can use Gemini to analyze images
- ✅ I receive YOLO detections
- ✅ I receive OCR text
- ✅ Results appear in Gemini

---

## **US-2: Process Videos via Gemini**
**As a user**  
I want to process videos using Gemini CLI  
So that I can get video analysis results without leaving Gemini.

**Acceptance Criteria:**
- ✅ I can submit videos via Gemini
- ✅ I receive job_id
- ✅ I can check status via Gemini
- ✅ I receive results via Gemini

---

## **US-3: Discover Available Tools**
**As a developer**  
I want to discover available MCP tools  
So that I know what the system can do.

**Acceptance Criteria:**
- ✅ I can call `/mcp/tools`
- ✅ I receive tool list
- ✅ Each tool has clear description
- ✅ Each tool has parameter schema

---

## **US-4: Consistent Plugin Architecture**
**As a developer**  
I want all plugins to follow the same structure  
So that I can maintain and extend them easily.

**Acceptance Criteria:**
- ✅ All plugins have valid manifests
- ✅ All plugins follow naming conventions
- ✅ All plugins implement correct signatures

---

## **US-5: Enforce Governance Rules**
**As a maintainer**  
I want CI to enforce governance rules  
So that code quality remains high.

**Acceptance Criteria:**
- ✅ CI validates folder structure
- ✅ CI validates naming conventions
- ✅ CI prevents forbidden vocabulary
- ✅ PRs cannot merge if governance fails

---

# 🛠️ 6. DEVELOPMENT PLAN — v1.0.0

## **Epic 1: MCP Server Implementation (8 commits)**

### **Commit 1: Create MCP Server Skeleton**
**Files Added:**
- `/mcp/server.py`
- `/mcp/__init__.py`

**Tests:**
- ✅ Server starts
- ✅ Server responds to `/mcp/health`

---

### **Commit 2: Implement Tool Registry**
**Files Added:**
- `/mcp/tool_registry.py`

**Tests:**
- ✅ Tool registry discovers tools
- ✅ Tool registry validates tool definitions

---

### **Commit 3: Implement Schema Generator**
**Files Added:**
- `/mcp/schema_generator.py`

**Tests:**
- ✅ Schema is generated correctly
- ✅ Schema is MCP-compliant

---

### **Commit 4: Implement /mcp/tools Endpoint**
**Files Changed:**
- `/mcp/server.py`

**Tests:**
- ✅ Endpoint returns tool list
- ✅ Tool list is correct

---

### **Commit 5: Implement /mcp/schema Endpoint**
**Files Changed:**
- `/mcp/server.py`

**Tests:**
- ✅ Endpoint returns schema
- ✅ Schema is valid

---

### **Commit 6: Implement Tool Executor**
**Files Added:**
- `/mcp/executor.py`

**Tests:**
- ✅ Executor runs tools
- ✅ Executor validates parameters
- ✅ Executor returns results

---

### **Commit 7: Implement /mcp/execute/{tool} Endpoint**
**Files Changed:**
- `/mcp/server.py`

**Tests:**
- ✅ Endpoint executes tools
- ✅ Image analysis works
- ✅ Video processing works

---

### **Commit 8: Add MCP Integration Tests**
**Files Added:**
- `/tests/mcp/test_server.py`
- `/tests/mcp/test_tools.py`

**Tests:**
- ✅ Full MCP flow works
- ✅ All tools work

---

## **Epic 2: Gemini-CLI Extension (5 commits)**

### **Commit 9: Create Extension Skeleton**
**Files Added:**
- `/gemini-cli-extension/mcp_client.py`
- `/gemini-cli-extension/__init__.py`

**Tests:**
- ✅ Extension initializes

---

### **Commit 10: Implement MCP Client**
**Files Changed:**
- `/gemini-cli-extension/mcp_client.py`

**Tests:**
- ✅ Client connects to server
- ✅ Client fetches tools
- ✅ Client fetches schema

---

### **Commit 11: Implement Tool Discovery**
**Files Changed:**
- `/gemini-cli-extension/mcp_client.py`

**Tests:**
- ✅ Extension discovers tools
- ✅ Tools are listed correctly

---

### **Commit 12: Implement Tool Execution**
**Files Changed:**
- `/gemini-cli-extension/mcp_client.py`

**Tests:**
- ✅ Extension executes tools
- ✅ Image analysis works
- ✅ Video processing works

---

### **Commit 13: Add Extension Integration Tests**
**Files Added:**
- `/gemini-cli-extension/tests/test_integration.py`

**Tests:**
- ✅ Full Gemini → MCP → Backend flow works

---

## **Epic 3: Architecture Cleanup (6 commits)**

### **Commit 14: Fix Plugin Manifests**
**Files Changed:**
- All `/plugins/*/manifest.yaml`

**Tests:**
- ✅ All manifests validate

---

### **Commit 15: Fix Plugin Types**
**Files Changed:**
- All `/plugins/*/manifest.yaml`

**Tests:**
- ✅ All plugin types are correct

---

### **Commit 16: Fix Tool Definitions**
**Files Changed:**
- All `/plugins/*/manifest.yaml`

**Tests:**
- ✅ All tool definitions are correct

---

### **Commit 17: Fix Plugin run() Signatures**
**Files Changed:**
- All `/plugins/*/__init__.py`

**Tests:**
- ✅ All signatures are consistent

---

### **Commit 18: Rebuild Pipeline Registry**
**Files Changed:**
- `/core/pipeline_registry.py`
- Pipeline configs

**Tests:**
- ✅ All pipelines load correctly

---

### **Commit 19: Normalize Folder Structure**
**Files Changed:**
- Move files to correct locations

**Tests:**
- ✅ All imports work
- ✅ All tests pass

---

## **Epic 4: Governance (4 commits)**

### **Commit 20: Add Folder Structure Validator**
**Files Added:**
- `/governance/validate_structure.py`
- `.github/workflows/governance.yml`

**Tests:**
- ✅ Validator works in CI

---

### **Commit 21: Add Naming Convention Validator**
**Files Added:**
- `/governance/validate_naming.py`

**Tests:**
- ✅ Validator works in CI

---

### **Commit 22: Add Forbidden Vocabulary Validator**
**Files Added:**
- `/governance/validate_vocabulary.py`

**Tests:**
- ✅ Validator works in CI

---

### **Commit 23: Add Contributor Guidelines**
**Files Added:**
- `/CONTRIBUTING.md`
- `/GOVERNANCE.md`

**Tests:**
- ✅ Documentation is clear

---

## **Epic 5: Documentation (2 commits)**

### **Commit 24: Add MCP Documentation**
**Files Added:**
- `/docs/mcp/api.md`
- `/docs/mcp/tools.md`
- `/docs/mcp/gemini-cli.md`

**Tests:**
- ✅ Documentation is complete

---

### **Commit 25: Update CHANGELOG and Release**
**Files Changed:**
- `/CHANGELOG.md`
- Version bump

**Tests:**
- ✅ All tests pass
- ✅ All features work
- ✅ Ready for v1.0.0 release

---

# 🔄 7. PULL REQUEST TEMPLATE — v1.0.0

```markdown
## PR Title
[v1.0.0 / Epic N / Commit M] Brief description

## Epic
Epic N: Epic Name

## Commit Number
Commit M of 25

## Description
What does this PR do?

## Why
Why is this change necessary?

## Files Changed
- `/path/to/file1.py`
- `/path/to/file2.ts`

## Tests Added/Modified
- ✅ Test 1 description
- ✅ Test 2 description

## Acceptance Criteria
- ✅ Criterion 1
- ✅ Criterion 2

## Backward Compatibility Check
- ✅ Phase 15 tests pass
- ✅ Phase 16 tests pass
- ✅ v0.9.0 tests pass
- ✅ Web UI works
- ✅ REST API works

## Governance Check
- ✅ Folder structure valid
- ✅ Naming conventions followed
- ✅ No forbidden vocabulary

## Related Issues
Part of v1.0.0 MCP integration

## Checklist
- [ ] Code follows project patterns
- [ ] Tests added/updated
- [ ] Documentation added/updated
- [ ] CHANGELOG updated (if final commit)
- [ ] No breaking changes
- [ ] All CI checks pass
- [ ] Ready for review
```

---

# ✅ FINAL SUMMARY

## **v0.9.0 Deliverables**
- ✅ Video upload to Web UI
- ✅ Job status tracking
- ✅ Job results display
- ✅ Full integration with Phase 16 async system
- ✅ 15 atomic commits
- ✅ Zero regressions

## **v1.0.0 Deliverables**
- ✅ MCP server
- ✅ MCP schema
- ✅ Tool registry
- ✅ Tool executor
- ✅ Gemini-CLI MCP extension
- ✅ Plugin architecture cleanup
- ✅ Pipeline registry cleanup
- ✅ Governance enforcement
- ✅ Complete documentation
- ✅ 25 atomic commits
- ✅ Production ready

---

**Roger, this is the complete, production-ready documentation for both v0.9.0 and v1.0.0. Everything is grounded in reality, fully detailed, and ready to implement.**