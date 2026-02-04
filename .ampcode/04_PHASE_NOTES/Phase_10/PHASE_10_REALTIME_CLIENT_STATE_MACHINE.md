# Phase 10 — RealtimeClient State Machine

Authoritative finite state machine for RealtimeClient.ts.

---

# 1. State Definitions

## IDLE

**Meaning:** Client initialized but not attempting connection.

**Entry Conditions:**
- Client freshly created
- User has not called `.connect()`

**Properties:**
- `isConnected()` returns `false`
- No timers running
- No WebSocket reference

**Exit Conditions:**
- User calls `.connect()`

---

## CONNECTING

**Meaning:** Attempting to establish WebSocket connection.

**Entry Conditions:**
- User calls `.connect()`
- Initial connection attempt or reconnection attempt (not first retry)

**Properties:**
- `isConnected()` returns `false`
- Connection timeout timer running (e.g., 10 seconds)
- WebSocket being created and opened

**Exit Conditions:**
- WebSocket `onopen` fires → CONNECTED
- WebSocket `onerror` fires → DISCONNECTED
- Connection timeout expires → DISCONNECTED
- User calls `.disconnect()` → CLOSED

---

## CONNECTED

**Meaning:** WebSocket connection active and ready for messages.

**Entry Conditions:**
- WebSocket `onopen` event fired
- Connection successfully established

**Properties:**
- `isConnected()` returns `true`
- Heartbeat timer running (ping/pong every 30 seconds)
- Receiving and dispatching messages
- Reconnect backoff counter reset to 0

**Exit Conditions:**
- WebSocket `onclose` fires (unexpected) → DISCONNECTED
- WebSocket `onerror` fires → DISCONNECTED
- User calls `.disconnect()` → CLOSED

**Special Behavior:**
- Automatically responds to `ping` messages with `pong`
- Validates all incoming messages
- Logs all errors and events
- Never blocks on message send

---

## DISCONNECTED

**Meaning:** Connection closed unexpectedly (not intentional close).

**Entry Conditions:**
- WebSocket `onclose` fired (not by user)
- WebSocket `onerror` fired
- Connection timeout while connecting
- Network error

**Properties:**
- `isConnected()` returns `false`
- Reconnect backoff timer scheduled
- Backoff delay calculated from current attempt count
- Backoff counter incremented

**Exit Conditions:**
- Backoff timer fires → RECONNECTING
- User calls `.disconnect()` → CLOSED
- Max reconnect attempts (5) exceeded → CLOSED

**Backoff Schedule:**
```
Attempt 1: 1 second
Attempt 2: 2 seconds
Attempt 3: 4 seconds
Attempt 4: 8 seconds
Attempt 5: 16 seconds
Attempt 6+: CLOSED (max attempts exceeded)
```

---

## RECONNECTING

**Meaning:** Attempting to reconnect after unexpected disconnect.

**Entry Conditions:**
- Backoff timer fired in DISCONNECTED state
- Attempt count < 5

**Properties:**
- `isConnected()` returns `false`
- Connection timeout timer running (10 seconds)
- WebSocket being created
- Attempting to reconnect with backoff

**Exit Conditions:**
- WebSocket `onopen` fires → CONNECTED
- WebSocket `onerror` fires → DISCONNECTED
- Connection timeout expires → DISCONNECTED
- User calls `.disconnect()` → CLOSED
- Max attempts reached → CLOSED

---

## CLOSED

**Meaning:** Client intentionally shut down by user.

**Entry Conditions:**
- User calls `.disconnect()`
- Max reconnect attempts (5) exceeded

**Properties:**
- `isConnected()` returns `false`
- No timers running
- WebSocket closed and dereferenced
- No further reconnection attempts

**Exit Conditions:**
- None (terminal state)
- Only option: create new RealtimeClient instance

---

# 2. State Transition Diagram

```
┌─────────────────────────────────────────────────────┐
│                  IDLE                               │
│  - No connection                                    │
│  - isConnected() = false                            │
└────────────┬──────────────────────────────────────┘
             │
             │ .connect()
             ▼
┌─────────────────────────────────────────────────────┐
│              CONNECTING                             │
│  - Attempting connection                            │
│  - Connection timeout timer: 10s                    │
│  - isConnected() = false                            │
└─┬───────────────────────────┬───────────────────┬──┘
  │                           │                   │
  │ onopen                    │ onerror/timeout   │ .disconnect()
  │                           │                   │
  ▼                           ▼                   ▼
┌────────────┐            ┌──────────────┐   ┌────────┐
│ CONNECTED  │            │ DISCONNECTED │   │ CLOSED │
│            │            │              │   │        │
│ onclose/   │            │ backoff      │   │ ─────► │ (Terminal)
│ onerror    │            │ timer: 1s    │   │        │
└─┬──────────┘            └──┬───────────┘   └────────┘
  │                          │
  │ .disconnect()            │ backoff timer fires
  │                          │
  ▼                          ▼
┌────────────┐            ┌──────────────┐
│ CLOSED     │            │ RECONNECTING │
│ (Terminal) │            │              │
│            │            │ timeout: 10s │
└────────────┘            │ attempt: N   │
                          └──┬───────────┘
                             │
                    ┌────────┴────────┬──────────────┐
                    │                 │              │
                    │ onopen          │ onerror/tm   │ .disconnect()
                    │                 │              │
                    ▼                 ▼              ▼
                 CONNECTED      DISCONNECTED    CLOSED
```

---

# 3. Transitions (Authoritative)

| From | To | Trigger | Action |
|------|----|---------| -------|
| IDLE | CONNECTING | `.connect()` | Create WebSocket, start timer |
| CONNECTING | CONNECTED | `onopen` | Reset backoff counter, emit connected=true |
| CONNECTING | DISCONNECTED | `onerror` or timeout | Increment backoff counter, schedule retry |
| CONNECTED | DISCONNECTED | `onclose` (unexpected) or `onerror` | Increment backoff counter, schedule retry |
| DISCONNECTED | RECONNECTING | Backoff timer fires | Create WebSocket, start connection timer |
| RECONNECTING | CONNECTED | `onopen` | Reset backoff counter, emit connected=true |
| RECONNECTING | DISCONNECTED | `onerror` or timeout | Increment backoff counter, schedule retry |
| ANY | CLOSED | `.disconnect()` called | Close WebSocket, clear all timers |
| DISCONNECTED | CLOSED | Attempt count = 5 | Clear all timers, emit error |

---

# 4. Message Handling per State

### IDLE
- No messages expected
- Any message received: Error logged

### CONNECTING
- No messages expected (not yet connected)
- Any message received: Log error, ignore

### CONNECTED
- All message types accepted
- `ping` → Auto-respond with `pong`
- `frame` → Dispatch to listeners
- `progress` → Dispatch to listeners
- `plugin_status` → Dispatch to listeners
- `warning` → Dispatch to listeners
- `error` → Dispatch to listeners
- Unknown type → Log warning, ignore
- Invalid JSON → Log error, ignore

### DISCONNECTED / RECONNECTING / CLOSED
- All messages ignored
- Incoming messages buffered briefly, then discarded

---

# 5. Timer Management

### CONNECTING State
- **Connection Timeout Timer:**
  - Duration: 10 seconds
  - On fire: Transition to DISCONNECTED
  - Cleared on: `onopen` (success) or `onerror` (explicit error)

### CONNECTED State
- **Heartbeat Timer:**
  - Duration: 30 seconds
  - On fire: Send `ping` message
  - Reset on: Successful message receive (not send)
  - Cleared on: Disconnect

### DISCONNECTED State
- **Backoff Timer:**
  - Duration: Exponential (1s, 2s, 4s, 8s, 16s)
  - On fire: Transition to RECONNECTING
  - Reset on: Successful reconnection
  - Max attempts: 5

### RECONNECTING State
- **Connection Timeout Timer:**
  - Duration: 10 seconds
  - Same as CONNECTING

---

# 6. Backoff Algorithm (Authoritative)

```typescript
const BACKOFF_DELAYS = [1000, 2000, 4000, 8000, 16000]; // ms
const MAX_ATTEMPTS = 5;

let attemptCount = 0;

function scheduleReconnect() {
  if (attemptCount >= MAX_ATTEMPTS) {
    // Max attempts exceeded, transition to CLOSED
    state = CLOSED;
    emit("error", "Max reconnection attempts exceeded");
    return;
  }
  
  const delay = BACKOFF_DELAYS[attemptCount];
  attemptCount++;
  
  // Add jitter: ±10%
  const jitter = delay * (Math.random() * 0.2 - 0.1);
  const finalDelay = delay + jitter;
  
  // Schedule reconnection
  reconnectTimer = setTimeout(() => {
    state = RECONNECTING;
    connect();
  }, finalDelay);
}

function onConnectSuccess() {
  attemptCount = 0;  // Reset on success
  state = CONNECTED;
  emit("connectionChange", true);
}
```

---

# 7. Error Handling by State

### IDLE
- Should not receive errors (nothing running)

### CONNECTING
- `onerror` → Log error, transition to DISCONNECTED
- Timeout → Log timeout, transition to DISCONNECTED

### CONNECTED
- `onerror` → Log error, transition to DISCONNECTED
- `onclose` → Log closure reason, transition to DISCONNECTED
- Invalid message → Log error, continue in CONNECTED

### DISCONNECTED
- No new errors expected (waiting for retry)

### RECONNECTING
- `onerror` → Log error, transition to DISCONNECTED
- Timeout → Log timeout, transition to DISCONNECTED

### CLOSED
- No further errors expected (terminal state)

---

# 8. Event Emissions

The state machine MUST emit:

### `connectionChange`
- **Fired on:** IDLE → CONNECTING → CONNECTED (true)
- **Fired on:** CONNECTED → DISCONNECTED → CLOSED (false)
- **Payload:** `boolean`

### `message`
- **Fired on:** `CONNECTED` when message received
- **Payload:** `RealtimeMessage`

### `error`
- **Fired on:** Any error condition
- **Payload:** `Error` object with `message` and `code`

### `reconnecting`
- **Fired on:** DISCONNECTED → RECONNECTING (attempt starts)
- **Payload:** `{ attempt: number, delay: number }`

---

# 9. Logging Requirements

All state transitions MUST be logged:

```typescript
// Example logging
console.log(`[RealtimeClient] Transition: ${prevState} → ${nextState}`);
console.log(`[RealtimeClient] CONNECTED: WebSocket ready`);
console.log(`[RealtimeClient] DISCONNECTED: Scheduling reconnect in 2000ms`);
console.log(`[RealtimeClient] Max reconnection attempts exceeded`);
```

---

# 10. Testing the State Machine

### Test Structure

```typescript
describe('RealtimeClient State Machine', () => {
  it('should transition IDLE → CONNECTING → CONNECTED', () => {
    // Test successful connection
  });
  
  it('should transition CONNECTED → DISCONNECTED → RECONNECTING → CONNECTED', () => {
    // Test reconnection after disconnect
  });
  
  it('should backoff correctly on repeated failures', () => {
    // Test backoff delays: 1s, 2s, 4s, 8s, 16s
  });
  
  it('should enter CLOSED after max attempts exceeded', () => {
    // Test 5 failed reconnects → CLOSED
  });
  
  it('should handle user disconnect in any state', () => {
    // Test .disconnect() from CONNECTING, CONNECTED, DISCONNECTED, RECONNECTING
  });
  
  it('should handle messages only in CONNECTED state', () => {
    // Test message handling per state
  });
});
```

---

# 11. Invariants

The state machine MUST maintain:

1. **Single Active Timer:** Only one timer per state
2. **Backoff Reset on Success:** Reconnect counter resets to 0 on successful connect
3. **No Overlapping Timers:** Timers cleared before starting new ones
4. **Terminal State:** CLOSED is terminal (no exits)
5. **Deterministic Transitions:** Same input → same next state always
6. **Error Messages:** All errors logged and emitted to listeners

---

# 12. Completion Criteria

The RealtimeClient state machine is complete when:

✅ All 7 states defined and implemented
✅ All transitions work as specified
✅ Backoff algorithm correct (1s, 2s, 4s, 8s, 16s)
✅ Max 5 reconnect attempts enforced
✅ Timers managed correctly (no leaks)
✅ Messages handled only in CONNECTED state
✅ All state transitions logged
✅ Events emitted correctly
✅ Error handling per state
✅ Tests pass for all transitions and edge cases

