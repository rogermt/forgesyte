# MCP JSON-RPC 2.0 Transport - Plan Review Summary

## Branch & Files
- **Branch**: `feature/mcp-jsonrpc-transport` (pushed to origin)
- **Plan Document**: `docs/implementation/MCP_JSONRPC_TRANSPORT_PLAN.md`
- **Issue Draft**: `ISSUE_12_DRAFT.md`

---

## The Problem

Gemini-CLI expects **JSON-RPC 2.0 protocol** but ForgeSyte only provides **REST API**.

```
Gemini-CLI sends:  POST /mcp (JSON-RPC)
ForgeSyte expects: GET /v1/mcp-manifest (REST)

Result: 405 Method Not Allowed
```

---

## The Solution

Implement a JSON-RPC 2.0 HTTP transport layer that:

1. **Accepts** `POST /mcp` with JSON-RPC payloads
2. **Implements** core MCP methods:
   - `initialize` - Server handshake
   - `tools/list` - List available tools
   - `tools/call` - Execute a tool
   - `ping` - Keep-alive
   - `resources/list` & `resources/read` (optional)

3. **Maintains** backwards compatibility with existing REST endpoints

---

## Implementation Plan: 6 Work Units (2-3 weeks)

### WU-01: JSON-RPC Core (2-3 days)
**Goal**: Build protocol layer
- Pydantic models for JSON-RPC requests/responses
- Request validation and error handling
- Transport handler framework

**Deliverable**: `server/app/mcp_jsonrpc.py`

---

### WU-02: Protocol Methods - Part 1 (2-3 days)
**Goal**: Core methods
- `initialize()` - capability exchange
- `tools/list()` - return available tools
- `ping()` - keep-alive

**Deliverable**: Method handlers using existing MCPAdapter

---

### WU-03: Protocol Methods - Part 2 (2-3 days)
**Goal**: Tool invocation
- `tools/call()` - execute plugin, create job, return result
- `resources/list()` - optional resource discovery
- `resources/read()` - optional resource fetching

**Deliverable**: Full tool invocation flow

---

### WU-04: HTTP Endpoint (2 days)
**Goal**: Wire up to FastAPI
- `POST /mcp` endpoint
- Request routing to handlers
- Session management

**Deliverable**: Working endpoint in `server/app/api.py`

---

### WU-05: Gemini-CLI Testing (2 days)
**Goal**: Verify with real client
- Integration tests with Gemini-CLI
- Manual testing script
- Documentation

**Deliverable**: Gemini-CLI working end-to-end

---

### WU-06: Optimization (1-2 days)
**Goal**: Performance & compatibility
- Caching for manifest/tool list
- Timeout handling for long-running tools
- Performance benchmarks

**Deliverable**: Production-ready optimization

---

## Architecture Diagram

```
┌─────────────────┐
│  Gemini-CLI     │
└────────┬────────┘
         │ POST /mcp (JSON-RPC)
         ▼
┌─────────────────────────────────┐
│  FastAPI Server                 │
├─────────────────────────────────┤
│  POST /mcp Endpoint (WU-04)     │
│  └─ JSONRPCTransport (WU-01)   │
│     ├─ initialize() (WU-02)    │
│     ├─ tools/list() (WU-02)    │
│     ├─ tools/call() (WU-03)    │
│     ├─ ping() (WU-02)          │
│     └─ resources/* (WU-03)     │
│         ▼
│  Existing Components (Issue #11)
│  ├─ MCPAdapter.get_manifest()
│  ├─ PluginManager
│  └─ Job System (/v1/analyze, /v1/jobs)
│         ▼
│  Plugins (OCR, Block Mapper, etc)
└─────────────────────────────────┘
```

---

## Example: Tool Invocation Flow

### Client Request (JSON-RPC)
```json
POST /mcp
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "vision.ocr",
    "arguments": {
      "image": "/path/to/image.png"
    }
  },
  "id": 1
}
```

### Server Response
```json
{
  "jsonrpc": "2.0",
  "result": {
    "output": "Extracted text from image"
  },
  "id": 1
}
```

### Internal Flow
1. `POST /mcp` endpoint receives request
2. JSONRPCTransport parses JSON-RPC
3. Routes to `tools/call()` handler
4. Handler extracts tool name and args
5. Calls existing `/v1/analyze` (REST)
6. Creates job, waits for completion
7. Returns result in JSON-RPC format

---

## Backwards Compatibility

**Existing REST endpoints kept**:
- `GET /v1/mcp-manifest` - unchanged
- `POST /v1/analyze` - unchanged
- `GET /v1/jobs/{id}` - unchanged

**New JSON-RPC endpoint**:
- `POST /mcp` - new, doesn't conflict

Clients can use either transport.

---

## Testing Strategy

**WU-01 Tests**:
- JSON-RPC validation
- Malformed request handling
- Pydantic model tests

**WU-02 Tests**:
- initialize() returns correct schema
- tools/list() returns valid tools
- ping() returns empty result

**WU-03 Tests**:
- tools/call() creates job
- tools/call() waits for result
- Error handling (invalid tool, etc)

**WU-04 Tests**:
- POST /mcp endpoint accepts requests
- Routes to correct handlers
- Returns JSON-RPC responses

**WU-05 Tests**:
- Gemini-CLI can discover server
- Gemini-CLI can list tools
- Gemini-CLI can invoke tools
- End-to-end workflow

**WU-06 Tests**:
- Performance benchmarks
- No regressions in Issue #11 tests
- Timeout handling works

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|-----------|
| JSON-RPC incompatible with Gemini-CLI | HIGH | Test with real Gemini-CLI in WU-05 |
| Break existing REST API | MEDIUM | Keep both endpoints, test backwards compat |
| Long-running tool timeout | MEDIUM | Implement timeout in WU-06 |
| Performance degradation | LOW | Add caching in WU-06 |
| Complex state management | MEDIUM | Use simple job polling pattern |

---

## Success Criteria

After WU-06, Gemini-CLI should:
- ✅ Discover ForgeSyte as MCP server
- ✅ List all available plugins as tools
- ✅ Invoke tools successfully
- ✅ Receive results in real time
- ✅ Handle errors gracefully

All existing REST functionality should:
- ✅ Continue working unchanged
- ✅ Pass all Issue #11 tests
- ✅ Have no regressions

---

## Timeline

```
Week 1:  WU-01 (JSON-RPC Core) + WU-02 (Methods Part 1)
Week 2:  WU-03 (Methods Part 2) + WU-04 (HTTP Endpoint)
Week 3:  WU-05 (Gemini-CLI Test) + WU-06 (Optimization)
```

Estimate: **11-15 days total** (~2-3 weeks)

---

## Ready for Review

**Please Review**:
1. ✅ Is 6 work units the right breakdown?
2. ✅ Are the work unit sizes reasonable (2-3 days each)?
3. ✅ Does the architecture make sense?
4. ✅ Are there missing requirements?
5. ✅ Should we adjust timeline or scope?

**Once Approved**:
1. Create GitHub Issue #12
2. Begin WU-01 implementation
3. Follow TDD approach (tests first)
4. Update Progress.md after each unit

---

## Questions for You

Before I begin implementation, please clarify:

1. **Async/Streaming**: Should `tools/call` wait for results or return job ID immediately?
   - Current plan: Wait for completion (simple)
   - Alternative: Return job ID, client polls (complex but responsive)

2. **Resource Methods**: Include `resources/list` and `resources/read` in scope?
   - Current plan: Optional, implement if time
   - Alternative: Exclude from v1, add later

3. **Authentication**: Add API key/token in this phase?
   - Current plan: No (out of scope)
   - Alternative: Add in WU-04

4. **Caching Strategy**: Redis or in-memory?
   - Current plan: In-memory with TTL (simple)
   - Alternative: Redis (requires external service)

---
