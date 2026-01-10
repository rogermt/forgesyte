# Issue #12: Implement MCP JSON-RPC 2.0 HTTP Transport

## Title
Implement MCP JSON-RPC 2.0 HTTP Transport for Gemini-CLI Integration

## Description

### Problem
ForgeSyte currently exposes MCP through REST endpoints (`/v1/mcp-manifest`, `/v1/analyze`). However, Gemini-CLI and other MCP clients expect the standard **JSON-RPC 2.0 HTTP transport** as defined by the [MCP specification](https://modelcontextprotocol.io/).

**Current Error**:
```
Error during discovery for MCP server 'forgesyte': Streamable HTTP error: 
Error POSTing to endpoint: {"detail":"Method Not Allowed"}
```

Gemini-CLI attempts to POST JSON-RPC messages to `/mcp`, but the server only accepts REST GET/POST to `/v1/` endpoints.

### Solution
Implement a JSON-RPC 2.0 HTTP transport layer that:
- Accepts POST requests to `/mcp` with JSON-RPC 2.0 payloads
- Implements required MCP protocol methods: `initialize`, `tools/list`, `tools/call`, `ping`
- Optionally implements resource methods: `resources/list`, `resources/read`
- Maintains backwards compatibility with existing REST endpoints

### Scope
This is a **follow-up to Issue #11** (MCP Adapter - COMPLETE).

**Out of Scope**:
- Streaming results (future enhancement)
- Resource subscriptions (future enhancement)
- Authentication/authorization (future phase)

---

## Implementation Plan

See: `docs/implementation/MCP_JSONRPC_TRANSPORT_PLAN.md`

**6 work units, ~2-3 weeks total**:

### WU-01: JSON-RPC 2.0 Transport Core (2-3 days)
- Pydantic models for JSON-RPC request/response
- Protocol validation and serialization
- Transport handler framework

### WU-02: MCP Protocol Methods - Part 1 (2-3 days)
- `initialize` method
- `tools/list` method
- `ping` method

### WU-03: MCP Protocol Methods - Part 2 (2-3 days)
- `tools/call` method with job creation
- `resources/list` method (optional)
- `resources/read` method (optional)

### WU-04: HTTP Endpoint and Session Management (2 days)
- POST `/mcp` endpoint
- Request routing
- Session management

### WU-05: Gemini-CLI Integration Testing (2 days)
- Integration tests with Gemini-CLI
- Manual testing script
- Updated documentation

### WU-06: Optimization and Backwards Compatibility (1-2 days)
- Response caching
- Timeout handling
- Performance benchmarks

---

## Expected Outcome

After completion:
- ✅ Gemini-CLI can discover ForgeSyte MCP server
- ✅ Gemini-CLI can list available tools
- ✅ Gemini-CLI can invoke tools and receive results
- ✅ Existing REST endpoints still functional
- ✅ 80%+ test coverage
- ✅ Documentation complete

---

## Files to be Modified/Created

**New**:
- `server/app/mcp_jsonrpc.py` - JSON-RPC protocol handler
- `server/app/mcp_transport.py` - HTTP transport layer
- `server/tests/test_mcp_jsonrpc.py` - Protocol tests
- `server/tests/test_mcp_transport.py` - Transport tests
- `docs/guides/MCP_JSONRPC_TRANSPORT.md` - Developer guide

**Modified**:
- `server/app/api.py` - Add POST /mcp endpoint
- `server/app/main.py` - Initialize transport
- `docs/guides/MCP_CONFIGURATION.md` - Add JSON-RPC section
- `README.md` - Update with JSON-RPC info

---

## Dependencies

- Depends on: #11 (MCP Adapter - COMPLETE ✅)
- No external dependencies needed

---

## Acceptance Criteria

- [ ] POST `/mcp` endpoint functional
- [ ] All JSON-RPC methods implemented and tested
- [ ] Gemini-CLI successfully discovers and uses ForgeSyte
- [ ] All existing REST endpoints still work
- [ ] 80%+ test coverage for new code
- [ ] All pre-commit hooks passing
- [ ] Documentation complete
- [ ] No regressions in #11 tests

---

## Labels
- `mcp`
- `json-rpc`
- `gemini-cli`
- `feature`
- `integration`

---

## Related
- Blocks: Gemini-CLI integration
- Depends on: #11 (MCP Adapter Implementation)
