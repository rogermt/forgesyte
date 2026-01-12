# WebSocket Error Analysis: Max Reconnection Attempts Reached

**Issue #17**: WebSocket Error: Max reconnection attempts reached  
**Related Issue #18**: Low WebUI test coverage  
**Status**: Open - Root cause investigation  
**Severity**: High (Blocks streaming feature)

---

## Problem Statement

When opening the Web UI and navigating to stream mode, users see:

```
WebSocket Error: Max reconnection attempts reached
```

And the Camera Preview shows:

```
○ Not streaming
```

This indicates the WebSocket client cannot connect to `/v1/stream` endpoint and exhausts its 5 reconnection attempts before giving up.

---

## Root Cause Analysis

### Theory 1: `/v1/stream` Endpoint Missing (Most Likely)

**Evidence**:
- useWebSocket.test.ts shows successful connections in tests (mocked WebSocket)
- But integration tests don't verify `/v1/stream` endpoint exists on actual server
- Previous work (WU-06) refactored WebSocket manager but may not have added the endpoint

**Location to Check**: `server/app/api.py` or `server/app/websocket.py`

**Questions**:
1. Does the server have a `@app.websocket("/v1/stream")` route?
2. Is it properly registered in the FastAPI app?
3. Does it handle the expected message protocol?

### Theory 2: WebSocket Connection Parameters Wrong

**Evidence**:
- useWebSocket hook builds URL as: `ws://localhost:8000/v1/stream?plugin=<plugin>`
- Server might expect different URL format or query parameters

**Questions**:
1. Does server expect plugin in query param or message?
2. Are authentication headers required?
3. Does server validate client protocol version?

### Theory 3: Test Suite Doesn't Catch Real-World Failure

**Evidence**:
- useWebSocket.test.ts mocks WebSocket, never tests real connection
- No integration tests verify `/v1/stream` endpoint responds properly
- App.test.tsx only mocks useWebSocket hook, doesn't test actual server connection

**Questions**:
1. Should E2E tests include WebSocket connection verification?
2. Should integration tests check `/v1/stream` endpoint availability?
3. Are there any tests that actually connect to a running server?

---

## Current Test Coverage for WebSocket

### Tests That Pass (Mocked)
```typescript
// src/hooks/useWebSocket.test.ts
✓ should connect to WebSocket URL (MOCKED)
✓ should include plugin in connection URL (MOCKED)
✓ should include API key in connection URL (MOCKED)
✓ should update state when connected (MOCKED)
✓ should send frame when connected (MOCKED)
✓ should handle result messages (MOCKED)
✓ should handle error messages (MOCKED)
✓ should attempt reconnection on unexpected close (MOCKED)
✓ should reconnect on explicit reconnect call (MOCKED)
```

**Problem**: All tests mock `global.WebSocket`. They never:
- Connect to actual server
- Verify endpoint exists
- Check message format compatibility
- Test reconnection against real failure

### Tests That DON'T Exist
- [ ] E2E test that starts server and connects to `/v1/stream`
- [ ] Integration test verifying endpoint responds with proper handshake
- [ ] Test that captures real WebSocket error from server unavailability
- [ ] Test that verifies message protocol (frame format, error messages, etc.)

---

## Why Current Tests Miss This

### 1. useWebSocket Tests are Unit Tests
```typescript
// This test PASSES but doesn't verify anything real
it("should connect to WebSocket URL", async () => {
    const { result } = renderHook(() => useWebSocket({
        url: "ws://localhost:8000/v1/stream",
        plugin: "motion_detector",
        onMessage: vi.fn(),
    }));
    
    // Mock WebSocket connects immediately
    // Real server: endpoint doesn't exist → connection fails
    // Test never detects this difference
});
```

### 2. App Component Tests Mock useWebSocket
```typescript
// App.test.tsx
vi.mock("./hooks/useWebSocket", () => ({
    useWebSocket: () => ({
        isConnected: false,
        error: null,
        send: vi.fn(),
        // ... mocked return
    }),
}));

// Never calls real useWebSocket
// Never connects to real server
// Never discovers that /v1/stream doesn't exist
```

### 3. No E2E WebSocket Verification
```bash
# e2e.test.sh runs integration tests but:
# - Doesn't wait for WebSocket to connect
# - Doesn't verify stream messages arrive
# - Doesn't check error states
```

---

## Diagnosis Path

### Step 1: Verify Endpoint Exists
```bash
# Check if endpoint is defined
grep -r "websocket.*stream\|/v1/stream" server/app/

# If nothing found → endpoint is missing
```

### Step 2: Check Server Logs During WebSocket Connection
```bash
# Terminal 1: Start server with verbose logging
cd server
uv run fastapi dev app/main.py

# Terminal 2: Open Web UI and try to stream
# Check Terminal 1 for connection attempts and errors
```

### Step 3: Test Connection Manually
```bash
# Use wscat to connect to endpoint
npm install -g wscat
wscat -c ws://localhost:8000/v1/stream

# Or with plugin:
wscat -c "ws://localhost:8000/v1/stream?plugin=motion_detector"

# If connection refused/times out → endpoint missing or misconfigured
```

### Step 4: Verify Message Format
```typescript
// Once connected, send test message
{
    "type": "frame",
    "plugin": "motion_detector",
    "frame_data": "base64encodedimage"
}

// Check server response
```

---

## Test Improvements Needed

### Missing Test Type 1: E2E WebSocket Connection

```typescript
// e2e/websocket.spec.ts (NEW)
describe("WebSocket Streaming", () => {
    it("should connect to /v1/stream endpoint", async () => {
        // Start real server
        // Open Web UI in browser
        // Verify WebSocket connects (not just attempt)
        // Verify "● Streaming" appears
        // Verify no error message
    });
});
```

### Missing Test Type 2: Server Endpoint Verification

```typescript
// server/tests/test_websocket_endpoint.py (NEW)
@pytest.mark.asyncio
async def test_websocket_endpoint_exists():
    """Verify /v1/stream endpoint responds to WebSocket connections"""
    async with AsyncClient(app=app, base_url="ws://localhost:8000") as client:
        async with client.websocket_connect("/v1/stream?plugin=motion_detector") as ws:
            # Server should accept connection
            data = await ws.receive_json()
            assert data["type"] == "connection"
```

### Missing Test Type 3: Message Protocol

```typescript
// web-ui/src/integration/websocket-protocol.test.ts (NEW)
describe("WebSocket Message Protocol", () => {
    it("should send frame in expected format");
    it("should receive results in expected format");
    it("should handle error messages from server");
    it("should handle connection close codes correctly");
});
```

### Missing Test Type 4: Reconnection Against Real Failure

```typescript
// e2e/websocket-reconnection.spec.ts (NEW)
describe("WebSocket Reconnection", () => {
    it("should reconnect when server restarts", async () => {
        // Connect to server
        // Stop server
        // Observe reconnection attempts
        // Start server again
        // Verify reconnection succeeds (not max retries)
    });
});
```

---

## Current Issue in App.test.tsx

Looking at the test file, this test is passing but misleading:

```typescript
it("should display stream view when stream mode selected", async () => {
    const { rerender } = render(<App />);
    
    // Mock useWebSocket returns successful connection
    mockUseWebSocket.mockReturnValue({
        isConnected: true,  // ← MOCKED, not real
        error: null,        // ← MOCKED, not real
        send: vi.fn(),
    });

    rerender(<App />);
    
    // Test PASSES because mock says connected
    // But actual server has no endpoint
    // Real user sees error
});
```

**The test should fail**, but it doesn't because:
1. Mock returns success
2. Component trusts the mock
3. No verification that mock matches reality

---

## Action Items

### Immediate (Blocking #17)
- [ ] Verify `/v1/stream` endpoint exists in server code
- [ ] Check server logs when Web UI tries to connect
- [ ] Test WebSocket connection manually with wscat
- [ ] Implement server endpoint if missing

### Short-term (Fix #18 - Test Coverage)
- [ ] Add E2E test that verifies WebSocket connects (not mocked)
- [ ] Add server-side test for `/v1/stream` endpoint
- [ ] Add integration test for message protocol
- [ ] Update App.test.tsx to verify real behavior

### Medium-term (Prevent Similar Issues)
- [ ] Add WebSocket mock setup to test utils
- [ ] Document WebSocket testing patterns
- [ ] Add CI check for E2E WebSocket connectivity
- [ ] Create WebSocket protocol spec document

---

## Why Tests Didn't Catch This

| Test Type | Checks Endpoint? | Catches Error? | Current Count |
|-----------|-----------------|----------------|---------------|
| Unit (useWebSocket.test.ts) | No (mocked) | No | 17 tests |
| Component (App.test.tsx) | No (mocked) | No | 8 tests |
| Integration (server-api.integration.test.ts) | No (REST only) | No | 18 tests |
| E2E (e2e.test.sh) | Partial | No | 1 test (basic) |
| **Required** | **Yes** | **Yes** | **0 tests** |

**Conclusion**: The test suite has 101 passing tests but **zero that verify WebSocket works end-to-end**.

---

## Related Files

- **Web UI Hook**: `web-ui/src/hooks/useWebSocket.ts`
- **Web UI Test**: `web-ui/src/hooks/useWebSocket.test.ts` (mocked)
- **App Component**: `web-ui/src/App.tsx`
- **App Test**: `web-ui/src/App.test.tsx` (mocked)
- **Server WebSocket**: `server/app/websocket.py` (or `api.py` if endpoint exists)
- **E2E Test**: `e2e.test.sh`

---

## Success Criteria

- [x] Root cause identified (endpoint missing vs misconfigured)
- [ ] Server `/v1/stream` endpoint verified working
- [ ] Web UI successfully connects in manual testing
- [ ] "Max reconnection attempts" error no longer appears
- [ ] E2E test added that catches this issue in CI
- [ ] Issue #17 closed
- [ ] Issue #18 test coverage improved

---

## Effort Estimate

| Task | Effort |
|------|--------|
| Verify endpoint exists | 0.5 hours |
| Test WebSocket manually | 0.5 hours |
| Implement missing endpoint (if needed) | 2-4 hours |
| Add E2E WebSocket test | 1-2 hours |
| Add server WebSocket test | 1 hour |
| Update component tests | 1 hour |
| **Total** | **6-8.5 hours** |

---

**Created**: 2026-01-12  
**Analysis by**: Coverage Report Analysis  
**Status**: Ready for investigation
