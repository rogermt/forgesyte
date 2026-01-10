# MCP JSON-RPC 2.0 Transport Implementation Plan (Issue #13)

**Status**: Planning  
**Start Date**: TBD  
**Target Completion**: TBD  
**Total Effort**: ~2-3 weeks (6 work units × 2-3 days each)  
**Dependency**: Issue #11 (MCP Adapter - COMPLETE)  
**GitHub Issue**: https://github.com/rogermt/forgesyte/issues/13

---

## Overview

This plan implements the **JSON-RPC 2.0 HTTP transport layer** required for Gemini-CLI and other MCP clients to discover and invoke ForgeSyte tools via the standard MCP protocol.

Currently, ForgeSyte exposes MCP through REST endpoints (`/v1/mcp-manifest`, `/v1/analyze`). The Gemini-CLI client expects:
- A `POST /mcp` endpoint
- JSON-RPC 2.0 protocol format
- Standard MCP methods: `initialize`, `tools/list`, `tools/call`, `ping`, `resources/list`, `resources/read`

**Reference**: [MCP Specification](https://modelcontextprotocol.io/)

---

## Context

### What Works (Issue #11 - Complete)
- ✅ MCP adapter with manifest generation
- ✅ Plugin metadata schema and validation
- ✅ REST endpoints: `/v1/mcp-manifest`, `/v1/mcp-version`, `/v1/analyze`
- ✅ 93 passing tests, 100% code coverage

### What's Missing (This Issue)
- ❌ JSON-RPC 2.0 HTTP transport layer
- ❌ MCP protocol method handlers
- ❌ Session/connection management
- ❌ Bidirectional tool invocation flow
- ❌ Resource listing (optional but good to have)

### Current Error
```
Error during discovery for MCP server 'forgesyte': Streamable HTTP error: 
Error POSTing to endpoint: {"detail":"Method Not Allowed"}
```

Cause: Gemini-CLI sends `POST /mcp` with JSON-RPC payload, but server only accepts `GET /v1/mcp-manifest`.

---

## Work Units

### WU-01: JSON-RPC 2.0 Transport Core (2-3 days)

**Goal**: Build the JSON-RPC 2.0 HTTP transport layer

**Deliverables**:
- `server/app/mcp_jsonrpc.py` - JSON-RPC 2.0 protocol handler
- `server/app/mcp_transport.py` - HTTP transport layer
- Pydantic models for JSON-RPC request/response
- Request/response validation and serialization

**Key Components**:
```python
# Pydantic models
class JSONRPCRequest(BaseModel):
    jsonrpc: str  # "2.0"
    method: str
    params: dict = {}
    id: Optional[Union[int, str]]

class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[dict] = None
    error: Optional[dict] = None
    id: Optional[Union[int, str]]

# Transport handler
class MCPTransport:
    async def handle_request(self, request: JSONRPCRequest) -> JSONRPCResponse
```

**Commits**:
1. `feat: Add JSON-RPC 2.0 protocol models and validation`
2. `feat: Implement JSON-RPC transport layer`

**Testing**:
- Unit tests for request/response validation
- Edge cases: invalid JSON, missing fields, malformed requests
- Pydantic validation tests

**Acceptance Criteria**:
- [ ] JSONRPCRequest validates required fields (jsonrpc, method, id)
- [ ] JSONRPCResponse serializes to valid JSON-RPC format
- [ ] Error responses include error code and message
- [ ] All validation tests pass
- [ ] Pre-commit hooks pass

---

### WU-02: MCP Protocol Methods - Part 1 (2-3 days)

**Goal**: Implement core MCP protocol methods

**Deliverables**:
- `initialize` method handler
- `tools/list` method handler
- `ping` method handler
- Protocol capability negotiation

**Methods**:
```python
async def handle_initialize(params: dict) -> dict:
    """Initialize server and exchange capabilities."""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}  # We support tools
        },
        "serverInfo": {
            "name": "forgesyte",
            "version": "0.1.0"
        }
    }

async def handle_tools_list() -> dict:
    """Return list of available tools."""
    # Use existing MCPAdapter.get_manifest()
    return {"tools": [...]}

async def handle_ping() -> dict:
    """Keep-alive check."""
    return {}
```

**Commits**:
1. `feat: Implement initialize method with capability exchange`
2. `feat: Implement tools/list method`
3. `feat: Implement ping method`

**Testing**:
- Unit tests for each method
- Test capability negotiation
- Test tool list format matches MCP schema
- Integration tests with JSONRPCTransport

**Acceptance Criteria**:
- [ ] initialize returns protocol version and server info
- [ ] tools/list returns valid tool array
- [ ] All methods return valid JSON-RPC responses
- [ ] Integration tests pass
- [ ] Coverage >80%

---

### WU-03: MCP Protocol Methods - Part 2 (2-3 days)

**Goal**: Implement tool invocation and resource methods

**Deliverables**:
- `tools/call` method handler
- `resources/list` method handler (optional)
- `resources/read` method handler (optional)
- Job creation and polling integration

**Methods**:
```python
async def handle_tools_call(params: dict) -> dict:
    """Execute a tool and return results."""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    # Create job via /v1/analyze
    # Wait for completion or return job ID
    # Return results in MCP format

async def handle_resources_list() -> dict:
    """List available resources (plugins, models, etc)."""
    return {"resources": [...]}

async def handle_resources_read(uri: str) -> dict:
    """Read resource content."""
    return {"contents": [...]}
```

**Commits**:
1. `feat: Implement tools/call method with job creation`
2. `feat: Implement resources/list method`
3. `feat: Implement resources/read method`

**Testing**:
- Unit tests for tool invocation
- Mock plugin execution
- Test error handling (invalid tools, execution failures)
- End-to-end test: initialize → tools/list → tools/call → result

**Acceptance Criteria**:
- [ ] tools/call creates job and returns result
- [ ] tools/call handles errors gracefully
- [ ] resources/list returns available resources
- [ ] E2E test passes (full MCP workflow)
- [ ] Coverage >80%

---

### WU-04: HTTP Endpoint and Session Management (2 days)

**Goal**: Add POST /mcp endpoint and manage client sessions

**Deliverables**:
- FastAPI endpoint: `POST /mcp`
- Session/connection management
- Request routing to protocol handlers
- Error handling and logging

**Commits**:
1. `feat: Add POST /mcp endpoint for JSON-RPC requests`
2. `feat: Implement session management for long-lived connections`

**Code**:
```python
@app.post("/mcp")
async def mcp_endpoint(request: Request) -> dict:
    """Handle JSON-RPC 2.0 MCP protocol requests."""
    try:
        payload = await request.json()
        rpc_request = JSONRPCRequest(**payload)
        
        # Route to appropriate handler
        response = await transport.handle_request(rpc_request)
        
        return response.model_dump(exclude_none=True)
    except ValidationError as e:
        return JSONRPCResponse(
            error={"code": -32602, "message": "Invalid params"},
            id=payload.get("id")
        ).model_dump()
```

**Testing**:
- Integration tests with FastAPI TestClient
- Test valid requests with various methods
- Test error responses (invalid JSON, missing fields)
- Test authentication/authorization (if added)

**Acceptance Criteria**:
- [ ] POST /mcp accepts JSON-RPC requests
- [ ] Requests routed to correct handlers
- [ ] Responses are valid JSON-RPC format
- [ ] All integration tests pass
- [ ] Endpoint documented

---

### WU-05: Gemini-CLI Integration Testing (2 days)

**Goal**: Test with Gemini-CLI and document integration

**Deliverables**:
- Integration tests with Gemini-CLI
- Manual testing script for JSON-RPC workflow
- Troubleshooting guide
- Updated documentation

**Commits**:
1. `test: Add Gemini-CLI integration tests`
2. `docs: Add JSON-RPC transport documentation`
3. `docs: Add Gemini-CLI integration guide`

**Testing**:
- Run Gemini-CLI against ForgeSyte server
- Test tool discovery
- Test tool invocation end-to-end
- Document any issues/workarounds

**Acceptance Criteria**:
- [ ] Gemini-CLI discovers ForgeSyte server
- [ ] Gemini-CLI lists available tools
- [ ] Gemini-CLI can invoke tools successfully
- [ ] Documentation complete
- [ ] Integration tests pass

---

### WU-06: Optimization and Backwards Compatibility (1-2 days)

**Goal**: Optimize performance and maintain REST endpoint compatibility

**Deliverables**:
- Response caching (manifest, tool list)
- Timeout handling for long-running tools
- Keep REST endpoints for direct API access
- Performance benchmarks
- Updated README

**Commits**:
1. `refactor: Add caching layer for manifest/tool list`
2. `feat: Add timeout handling for tool invocation`
3. `docs: Update README with JSON-RPC transport info`

**Testing**:
- Performance tests with concurrent requests
- Timeout tests
- Backwards compatibility tests (REST endpoints still work)
- Load testing

**Acceptance Criteria**:
- [ ] Manifest caching reduces response time
- [ ] Timeout handling prevents hung requests
- [ ] REST endpoints still functional
- [ ] No regression in existing tests
- [ ] Performance benchmarks documented

---

## Implementation Strategy

### Architecture Overview

```
Gemini-CLI
    ↓ (POST /mcp with JSON-RPC)
FastAPI Server
    ↓
POST /mcp Endpoint
    ↓
JSONRPCTransport (WU-01)
    ↓
Protocol Methods (WU-02, WU-03)
    ├→ initialize()
    ├→ tools/list()
    ├→ tools/call()
    ├→ ping()
    └→ resources/* (optional)
    ↓
Existing Components
    ├→ MCPAdapter (Issue #11)
    ├→ PluginManager
    └→ Job System (/v1/analyze, /v1/jobs)
```

### Data Flow for Tool Invocation

```
1. Gemini-CLI sends: POST /mcp
   {
     "jsonrpc": "2.0",
     "method": "tools/call",
     "params": {"name": "vision.ocr", "arguments": {"image": "..."}},
     "id": 1
   }

2. Server routes to tools/call handler
3. Handler calls existing /v1/analyze endpoint
4. Creates job, returns job_id
5. Server polls /v1/jobs/job_id
6. Returns result in JSON-RPC format:
   {
     "jsonrpc": "2.0",
     "result": {"output": "..."},
     "id": 1
   }
```

### Backwards Compatibility

Keep existing endpoints:
- `GET /v1/mcp-manifest` - Static discovery
- `POST /v1/analyze` - Direct tool invocation
- `GET /v1/jobs/{id}` - Job status

Add new endpoint:
- `POST /mcp` - JSON-RPC 2.0 transport

Both can coexist; clients choose which to use.

---

## Dependencies & Prerequisites

**Required Before Starting**:
- [ ] Issue #11 (MCP Adapter) complete and merged ✅ DONE
- [ ] FastAPI app structure stable
- [ ] Plugin system working correctly
- [ ] Job system functional

**External Dependencies**:
- None (using existing: FastAPI, Pydantic, httpx)

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| JSON-RPC serialization errors | Comprehensive Pydantic models and validation |
| Protocol incompatibility with Gemini-CLI | Test with actual Gemini-CLI early (WU-05) |
| Breaking existing REST API | Keep both endpoints, test backwards compat |
| Long-running tool timeouts | Implement timeout handling in WU-06 |
| Performance degradation | Add caching layer, benchmark (WU-06) |

---

## Success Metrics

✅ **Completion Checklist**:
- [ ] All 6 work units completed
- [ ] POST /mcp endpoint functional
- [ ] All JSON-RPC methods implemented
- [ ] Gemini-CLI successfully discovers and invokes tools
- [ ] 80%+ test coverage for new code
- [ ] All pre-commit hooks passing
- [ ] Documentation complete
- [ ] No regressions in existing endpoints

---

## Timeline (Estimated)

| WU | Effort | Week | Status |
|----|--------|------|--------|
| WU-01 | 2-3 days | 1 | Planned |
| WU-02 | 2-3 days | 1-2 | Planned |
| WU-03 | 2-3 days | 2 | Planned |
| WU-04 | 2 days | 2 | Planned |
| WU-05 | 2 days | 3 | Planned |
| WU-06 | 1-2 days | 3 | Planned |
| **Total** | **11-15 days** | **3 weeks** | **Planned** |

---

## Related Issues

- **#11**: MCP Adapter and Gemini integration (COMPLETE)
- **#13**: MCP JSON-RPC 2.0 Transport (this issue)

---

## Notes

### Why This Approach?

1. **Modular**: Each WU is independently testable
2. **Incremental**: Can integrate with Gemini-CLI early (WU-05)
3. **Backwards Compatible**: REST endpoints remain unchanged
4. **Focused**: Each unit has clear acceptance criteria
5. **Testable**: Comprehensive tests at each stage

### Future Enhancements

After this phase:
- Streaming tool results (Server-Sent Events)
- Resource subscriptions
- Tool capability negotiation
- Rate limiting per client
- Authentication/authorization
- Metrics and monitoring

---
