# v0.10.0 Implementation Plan — ForgeSyte Repository

**Status:** Draft
**Last Updated:** 2026-02-26
**Branch:** `v0.10.0`
**Base Branch:** `main`
**Discussion:** https://github.com/rogermt/forgesyte/discussions/226
**Design Doc:** `./DESIGN.md`

---

## 1. Overview

This plan covers **ForgeSyte repository** changes for v0.10.0 Streaming Video Analysis.

### Scope

| Phase | Focus | Priority |
|-------|-------|----------|
| 4 | Create `progress.py` + unit tests | High |
| 5 | Create `/ws/jobs/{job_id}` WebSocket endpoint + tests | High |
| 6 | Update `worker.py` for WebSocket progress broadcast | High |
| 7 | Create `useJobProgress.ts` hook + tests | High |
| 8 | Update `JobStatus.tsx` for WebSocket + fallback | High |
| 9 | Integration tests | Medium |
| 10 | E2E validation | Medium |

**Note:** Phases 1-3 are in ForgeSyte-Plugins repository. See `/home/rogermt/forgesyte-plugins/docs/releases/v0.10.0/PLAN.md`.

---

## 2. Prerequisites

### 2.1 Current State (Verified GREEN)

```bash
# Run from ForgeSyte root
cd /home/rogermt/forgesyte

# Server checks
cd server && uv run pytest tests/ -v --tb=short
cd .. && uv run pre-commit run --all-files
python scripts/scan_execution_violations.py

# Web-UI checks
cd web-ui
npm run lint
npm run type-check
npm run test -- --run
```

All must PASS before starting Phase 4.

### 2.2 Branch Setup

```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b v0.10.0

# Verify branch
git branch --show-current  # Should show: v0.10.0
```

---

## 3. TDD Workflow (Per Phase)

```
┌─────────────────────────────────────────────────────────────┐
│  1. Write failing tests FIRST                              │
│  2. Run tests → confirm RED                                │
│  3. Implement minimum code to pass                         │
│  4. Run tests → confirm GREEN                              │
│  5. Run pre-commit verification                            │
│  6. Commit with descriptive message                        │
│  7. Save outputs to .log files                             │
└─────────────────────────────────────────────────────────────┘
```

### Output Logging

All outputs saved to: `/home/rogermt/forgesyte/docs/releases/v0.10.0/logs/`

```bash
# Create logs directory
mkdir -p /home/rogermt/forgesyte/docs/releases/v0.10.0/logs

# Example usage
cd /home/rogermt/forgesyte/server
uv run pytest tests/unit/test_progress.py -v 2>&1 | tee ../docs/releases/v0.10.0/logs/phase4_tests.log
```

---

## 4. Phase Details

---

## Phase 4: Create Progress Module + Unit Tests

**Goal:** Create `progress.py` with WebSocket broadcast functionality.

### 4.1 Files to Create

| File | Purpose |
|------|---------|
| `server/app/workers/progress.py` | Progress callback with WebSocket broadcast |
| `server/tests/unit/test_progress.py` | Unit tests for progress module |

### 4.2 Test Specifications

```python
# tests/unit/test_progress.py

import pytest
from app.workers.progress import progress_callback, ProgressEvent

class TestProgressCallback:
    """Unit tests for progress callback functionality."""
    
    def test_progress_event_creation(self):
        """Test ProgressEvent dataclass creation."""
        event = ProgressEvent(
            job_id="test-123",
            current_frame=50,
            total_frames=100,
        )
        assert event.job_id == "test-123"
        assert event.current_frame == 50
        assert event.total_frames == 100
        assert event.percent == 50
    
    def test_percent_calculation_zero_total(self):
        """Test percent is 0 when total is 0."""
        event = ProgressEvent(
            job_id="test-123",
            current_frame=0,
            total_frames=0,
        )
        assert event.percent == 0
    
    def test_percent_calculation_rounds_down(self):
        """Test percent calculation rounds down."""
        event = ProgressEvent(
            job_id="test-123",
            current_frame=1,
            total_frames=3,
        )
        assert event.percent == 33  # int(33.33...) = 33
    
    def test_percent_reaches_100(self):
        """Test percent reaches 100 at completion."""
        event = ProgressEvent(
            job_id="test-123",
            current_frame=100,
            total_frames=100,
        )
        assert event.percent == 100
    
    def test_progress_callback_to_dict(self):
        """Test serialization to dict for WebSocket broadcast."""
        event = ProgressEvent(
            job_id="test-123",
            current_frame=50,
            total_frames=100,
        )
        result = event.to_dict()
        assert result == {
            "job_id": "test-123",
            "current_frame": 50,
            "total_frames": 100,
            "percent": 50,
        }
```

### 4.3 Implementation

```python
# server/app/workers/progress.py
"""
Progress callback module for WebSocket job progress streaming.

v0.10.0: Emits real-time progress events for video jobs.
"""

from dataclasses import dataclass
from typing import Optional
import asyncio

from app.websocket_manager import ws_manager


@dataclass
class ProgressEvent:
    """Progress event for video job processing."""
    
    job_id: str
    current_frame: int
    total_frames: int
    
    @property
    def percent(self) -> int:
        """Calculate percentage (0-100)."""
        if self.total_frames <= 0:
            return 0
        return int((self.current_frame / self.total_frames) * 100)
    
    def to_dict(self) -> dict:
        """Serialize to dict for WebSocket broadcast."""
        return {
            "job_id": self.job_id,
            "current_frame": self.current_frame,
            "total_frames": self.total_frames,
            "percent": self.percent,
        }


def progress_callback(
    job_id: str,
    current_frame: int,
    total_frames: int,
) -> ProgressEvent:
    """
    Create progress event and broadcast via WebSocket.
    
    Called by worker during video processing to emit real-time progress.
    
    Args:
        job_id: Job UUID string
        current_frame: Current frame number being processed
        total_frames: Total frames in video
        
    Returns:
        ProgressEvent that was broadcast
    """
    event = ProgressEvent(
        job_id=job_id,
        current_frame=current_frame,
        total_frames=total_frames,
    )
    
    # Broadcast to job topic subscribers
    # Note: ws_manager.broadcast handles async internally
    asyncio.create_task(
        ws_manager.broadcast(
            event.to_dict(),
            topic=f"job:{job_id}"
        )
    )
    
    return event
```

### 4.4 Verification Commands

```bash
# From ForgeSyte root
cd /home/rogermt/forgesyte

# 1. Run unit tests (should be RED initially, then GREEN)
cd server
uv run pytest tests/unit/test_progress.py -v 2>&1 | tee ../docs/releases/v0.10.0/logs/phase4_tests.log

# 2. Run all server tests
uv run pytest tests/ -v --tb=short 2>&1 | tee ../docs/releases/v0.10.0/logs/phase4_all_tests.log

# 3. Run pre-commit
cd ..
uv run pre-commit run --all-files 2>&1 | tee docs/releases/v0.10.0/logs/phase4_precommit.log

# 4. Run governance check
python scripts/scan_execution_violations.py 2>&1 | tee docs/releases/v0.10.0/logs/phase4_governance.log
```

### 4.5 Commit

```bash
git add server/app/workers/progress.py server/tests/unit/test_progress.py
git commit -m "feat(server): add progress callback module for WebSocket streaming

- Add ProgressEvent dataclass with percent calculation
- Add progress_callback() for worker integration
- Unit tests for progress event creation and serialization

Phase 4 of v0.10.0 implementation."
```

---

## Phase 5: Create WebSocket Job Progress Endpoint

**Goal:** Create `/ws/jobs/{job_id}` WebSocket endpoint for job progress streaming.

### 5.1 Files to Create/Modify

| File | Purpose |
|------|---------|
| `server/app/realtime/job_progress_router.py` | NEW: WebSocket endpoint for job progress |
| `server/tests/api/test_job_progress_ws.py` | NEW: WebSocket endpoint tests |
| `server/app/main.py` | MODIFY: Register new router |

### 5.2 Test Specifications

```python
# tests/api/test_job_progress_ws.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

class TestJobProgressWebSocket:
    """Tests for /ws/jobs/{job_id} WebSocket endpoint."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_websocket_connect(self, client):
        """Test WebSocket connection is accepted."""
        with client.websocket_connect("/ws/jobs/test-job-123") as websocket:
            # Connection should be accepted
            assert websocket is not None
    
    def test_websocket_ping_pong(self, client):
        """Test ping/pong message handling."""
        with client.websocket_connect("/ws/jobs/test-job-123") as websocket:
            websocket.send_json({"type": "ping"})
            response = websocket.receive_json()
            assert response["type"] == "pong"
    
    def test_websocket_receives_progress_event(self, client):
        """Test receiving progress event on subscribed job."""
        import asyncio
        from app.workers.progress import progress_callback
        
        with client.websocket_connect("/ws/jobs/test-job-456") as websocket:
            # Trigger progress callback
            asyncio.run(progress_callback("test-job-456", 50, 100))
            
            # Should receive the progress event
            response = websocket.receive_json()
            assert response["job_id"] == "test-job-456"
            assert response["current_frame"] == 50
            assert response["total_frames"] == 100
            assert response["percent"] == 50
    
    def test_websocket_ignores_other_jobs(self, client):
        """Test that events for other jobs are not received."""
        import asyncio
        from app.workers.progress import progress_callback
        
        with client.websocket_connect("/ws/jobs/job-A") as websocket:
            # Send progress for different job
            asyncio.run(progress_callback("job-B", 50, 100))
            
            # Send ping to check connection is alive
            websocket.send_json({"type": "ping"})
            response = websocket.receive_json()
            assert response["type"] == "pong"
```

### 5.3 Implementation

```python
# server/app/realtime/job_progress_router.py
"""
WebSocket endpoint for job progress streaming.

v0.10.0: Real-time progress updates for video jobs.
"""

import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket_manager import ws_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/jobs/{job_id}")
async def job_progress_websocket(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time job progress updates.
    
    Client subscribes to this endpoint to receive progress events
    for a specific job.
    
    Message Types:
    - Client sends: {"type": "ping"}
    - Server sends: {"type": "pong"} or progress events
    
    Progress Event Format:
    {
        "job_id": "uuid-string",
        "current_frame": 189,
        "total_frames": 450,
        "percent": 42
    }
    """
    client_id = f"job-{job_id}-{uuid.uuid4()}"
    
    # Accept connection
    await ws_manager.connect(websocket, client_id)
    
    # Subscribe to job topic
    await ws_manager.subscribe(client_id, f"job:{job_id}")
    
    try:
        while True:
            # Wait for client messages (ping/pong, etc.)
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        await ws_manager.unsubscribe(client_id, f"job:{job_id}")
        await ws_manager.disconnect(client_id)
```

### 5.4 Register Router in main.py

```python
# In server/app/main.py
# Add import at top:
from app.realtime.job_progress_router import router as job_progress_router

# Add router registration (after other routers):
app.include_router(job_progress_router)
```

### 5.5 Verification Commands

```bash
# From ForgeSyte root
cd /home/rogermt/forgesyte

# 1. Run WebSocket tests
cd server
uv run pytest tests/api/test_job_progress_ws.py -v 2>&1 | tee ../docs/releases/v0.10.0/logs/phase5_tests.log

# 2. Run all tests
uv run pytest tests/ -v --tb=short 2>&1 | tee ../docs/releases/v0.10.0/logs/phase5_all_tests.log

# 3. Run pre-commit
cd ..
uv run pre-commit run --all-files 2>&1 | tee docs/releases/v0.10.0/logs/phase5_precommit.log

# 4. Run governance check
python scripts/scan_execution_violations.py 2>&1 | tee docs/releases/v0.10.0/logs/phase5_governance.log
```

### 5.6 Commit

```bash
git add server/app/realtime/job_progress_router.py \
        server/tests/api/test_job_progress_ws.py \
        server/app/main.py

git commit -m "feat(server): add WebSocket endpoint for job progress streaming

- Add /ws/jobs/{job_id} WebSocket endpoint
- Subscribe to job topic for progress events
- Unit tests for WebSocket connection and message handling

Phase 5 of v0.10.0 implementation."
```

---

## Phase 6: Update Worker for WebSocket Progress Broadcast

**Goal:** Integrate WebSocket broadcasting into worker progress updates.

### 6.1 Files to Modify

| File | Purpose |
|------|---------|
| `server/app/workers/worker.py` | MODIFY: Add WebSocket broadcast to `_update_job_progress()` |

### 6.2 Test Specifications

```python
# tests/unit/test_worker_progress_broadcast.py

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.workers.worker import JobWorker

class TestWorkerProgressBroadcast:
    """Tests for worker WebSocket progress broadcasting."""
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()
    
    @pytest.mark.asyncio
    async def test_update_job_progress_broadcasts_to_websocket(self, mock_db):
        """Test that _update_job_progress broadcasts via WebSocket."""
        with patch('app.workers.worker.ws_manager') as mock_ws:
            mock_ws.broadcast = AsyncMock()
            
            worker = JobWorker()
            worker._update_job_progress(
                job_id="test-job-123",
                current_frame=50,
                total_frames=100,
                db=mock_db,
            )
            
            # Should have called broadcast
            mock_ws.broadcast.assert_called_once()
            call_args = mock_ws.broadcast.call_args
            assert call_args[1]["topic"] == "job:test-job-123"
            
            event = call_args[0][0]
            assert event["job_id"] == "test-job-123"
            assert event["current_frame"] == 50
            assert event["percent"] == 50
    
    @pytest.mark.asyncio
    async def test_progress_throttling_still_works(self, mock_db):
        """Test that 5% throttling still applies to DB updates."""
        worker = JobWorker()
        
        with patch('app.workers.worker.ws_manager') as mock_ws:
            mock_ws.broadcast = AsyncMock()
            
            # First call at 0%
            worker._update_job_progress("job-1", 0, 100, mock_db)
            assert mock_db.commit.call_count >= 1
            
            # Reset mock
            mock_db.reset_mock()
            
            # Call at 3% (should be throttled for DB but still broadcast)
            worker._update_job_progress("job-1", 3, 100, mock_db)
            # Broadcast should still happen
            assert mock_ws.broadcast.called
```

### 6.3 Implementation Changes

```python
# In server/app/workers/worker.py

# Add import at top:
from app.websocket_manager import ws_manager

# Modify _update_job_progress() method (around line 102):

def _update_job_progress(
    self,
    job_id: str,
    current_frame: int,
    total_frames: int,
    db,
    tool_index: int = 0,
    total_tools: int = 1,
    tool_name: str = "",
) -> None:
    """
    Update job progress in database and broadcast via WebSocket.
    
    v0.10.0: Now also broadcasts progress events via WebSocket.
    DB updates are still throttled to every 5% for performance.
    """
    # Calculate overall progress
    if total_tools > 1:
        tool_progress = (current_frame / total_frames) * 100 if total_frames > 0 else 0
        overall_progress = ((tool_index * 100) + tool_progress) / total_tools
        percent = int(overall_progress)
    else:
        percent = int((current_frame / total_frames) * 100) if total_frames > 0 else 0
    
    # Always broadcast via WebSocket (v0.10.0)
    import asyncio
    asyncio.create_task(
        ws_manager.broadcast(
            {
                "job_id": job_id,
                "current_frame": current_frame,
                "total_frames": total_frames,
                "percent": percent,
                "current_tool": tool_name,
                "tools_total": total_tools,
                "tools_completed": tool_index,
            },
            topic=f"job:{job_id}"
        )
    )
    
    # DB update: Throttled to every 5% (existing behavior)
    if self._last_progress_percent is not None:
        if abs(percent - self._last_progress_percent) < 5:
            return  # Skip DB update
    
    self._last_progress_percent = percent
    
    # Update job in database (existing code continues...)
    # ...
```

### 6.4 Verification Commands

```bash
# From ForgeSyte root
cd /home/rogermt/forgesyte

# 1. Run worker tests
cd server
uv run pytest tests/unit/test_worker_progress_broadcast.py -v 2>&1 | tee ../docs/releases/v0.10.0/logs/phase6_tests.log

# 2. Run all tests
uv run pytest tests/ -v --tb=short 2>&1 | tee ../docs/releases/v0.10.0/logs/phase6_all_tests.log

# 3. Run pre-commit
cd ..
uv run pre-commit run --all-files 2>&1 | tee docs/releases/v0.10.0/logs/phase6_precommit.log

# 4. Run governance check
python scripts/scan_execution_violations.py 2>&1 | tee docs/releases/v0.10.0/logs/phase6_governance.log
```

### 6.5 Commit

```bash
git add server/app/workers/worker.py \
        server/tests/unit/test_worker_progress_broadcast.py

git commit -m "feat(server): add WebSocket broadcast to worker progress updates

- Broadcast progress events via WebSocket on every frame
- Keep DB update throttling at 5% for performance
- Unit tests for broadcast functionality

Phase 6 of v0.10.0 implementation."
```

---

## Phase 7: Create useJobProgress Hook

**Goal:** Create React hook for subscribing to job progress via WebSocket.

### 7.1 Files to Create

| File | Purpose |
|------|---------|
| `web-ui/src/hooks/useJobProgress.ts` | NEW: React hook for WebSocket job progress |
| `web-ui/src/hooks/__tests__/useJobProgress.test.ts` | NEW: Unit tests for hook |

### 7.2 Test Specifications

```typescript
// web-ui/src/hooks/__tests__/useJobProgress.test.ts

import { renderHook, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useJobProgress } from '../useJobProgress';

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  url: string;
  readyState: number = WebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      this.onopen?.(new Event('open'));
    }, 0);
  }

  send(data: string) {}
  close() {
    this.readyState = WebSocket.CLOSED;
    this.onclose?.(new CloseEvent('close'));
  }

  static simulateMessage(data: object) {
    MockWebSocket.instances.forEach(ws => {
      ws.onmessage?.(new MessageEvent('message', { data: JSON.stringify(data) }));
    });
  }
}

vi.stubGlobal('WebSocket', MockWebSocket);

describe('useJobProgress', () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns null progress initially', () => {
    const { result } = renderHook(() => useJobProgress('job-123'));
    expect(result.current.progress).toBeNull();
    expect(result.current.status).toBe('pending');
  });

  it('updates progress on WebSocket message', async () => {
    const { result } = renderHook(() => useJobProgress('job-123'));

    // Simulate WebSocket message
    act(() => {
      MockWebSocket.simulateMessage({
        job_id: 'job-123',
        current_frame: 50,
        total_frames: 100,
        percent: 50,
      });
    });

    await waitFor(() => {
      expect(result.current.progress).toEqual({
        job_id: 'job-123',
        current_frame: 50,
        total_frames: 100,
        percent: 50,
      });
      expect(result.current.status).toBe('running');
    });
  });

  it('sets status to completed on completion event', async () => {
    const { result } = renderHook(() => useJobProgress('job-123'));

    act(() => {
      MockWebSocket.simulateMessage({ status: 'completed', job_id: 'job-123' });
    });

    await waitFor(() => {
      expect(result.current.status).toBe('completed');
    });
  });

  it('sets status to failed on error event', async () => {
    const { result } = renderHook(() => useJobProgress('job-123'));

    act(() => {
      MockWebSocket.simulateMessage({
        status: 'error',
        job_id: 'job-123',
        message: 'Processing failed'
      });
    });

    await waitFor(() => {
      expect(result.current.status).toBe('failed');
      expect(result.current.error).toBe('Processing failed');
    });
  });

  it('ignores messages for other jobs', async () => {
    const { result } = renderHook(() => useJobProgress('job-A'));

    act(() => {
      MockWebSocket.simulateMessage({
        job_id: 'job-B',  // Different job
        current_frame: 50,
        total_frames: 100,
        percent: 50,
      });
    });

    // Progress should remain null
    expect(result.current.progress).toBeNull();
  });

  it('cleans up WebSocket on unmount', () => {
    const { unmount } = renderHook(() => useJobProgress('job-123'));
    
    expect(MockWebSocket.instances.length).toBeGreaterThan(0);
    const ws = MockWebSocket.instances[0];
    
    unmount();
    
    expect(ws.readyState).toBe(WebSocket.CLOSED);
  });
});
```

### 7.3 Implementation

```typescript
// web-ui/src/hooks/useJobProgress.ts
/**
 * React hook for subscribing to job progress via WebSocket.
 *
 * v0.10.0: Real-time progress streaming for video jobs.
 */

import { useEffect, useState, useCallback, useRef } from 'react';

export interface ProgressEvent {
  job_id: string;
  current_frame: number;
  total_frames: number;
  percent: number;
  current_tool?: string;
  tools_total?: number;
  tools_completed?: number;
}

export interface UseJobProgressResult {
  progress: ProgressEvent | null;
  status: 'pending' | 'running' | 'completed' | 'failed';
  error: string | null;
  isConnected: boolean;
}

export function useJobProgress(jobId: string | null): UseJobProgressResult {
  const [progress, setProgress] = useState<ProgressEvent | null>(null);
  const [status, setStatus] = useState<'pending' | 'running' | 'completed' | 'failed'>('pending');
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const connect = useCallback(() => {
    if (!jobId) return;

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/jobs/${jobId}`;
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Ignore messages for other jobs
        if (data.job_id && data.job_id !== jobId) return;

        // Handle completion
        if (data.status === 'completed') {
          setStatus('completed');
          return;
        }

        // Handle error
        if (data.status === 'error') {
          setStatus('failed');
          setError(data.message || 'Job failed');
          return;
        }

        // Handle progress
        if (data.current_frame !== undefined) {
          setProgress(data);
          setStatus('running');
        }

        // Handle pong (keepalive)
        if (data.type === 'pong') {
          // Connection is alive
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      // Attempt reconnect after 2 seconds
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connect();
      }, 2000);
    };

    ws.onerror = () => {
      setError('WebSocket connection error');
    };
  }, [jobId]);

  useEffect(() => {
    if (!jobId) {
      // Reset state when jobId is null
      setProgress(null);
      setStatus('pending');
      setError(null);
      setIsConnected(false);
      return;
    }

    connect();

    // Cleanup on unmount or jobId change
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, [jobId, connect]);

  // Send periodic pings to keep connection alive
  useEffect(() => {
    if (!isConnected || !wsRef.current) return;

    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // Every 30 seconds

    return () => clearInterval(pingInterval);
  }, [isConnected]);

  return {
    progress,
    status,
    error,
    isConnected,
  };
}
```

### 7.4 Verification Commands

```bash
# From ForgeSyte root
cd /home/rogermt/forgesyte/web-ui

# 1. Run hook tests
npm run test -- --run src/hooks/__tests__/useJobProgress.test.ts 2>&1 | tee ../docs/releases/v0.10.0/logs/phase7_tests.log

# 2. Run all tests
npm run test -- --run 2>&1 | tee ../docs/releases/v0.10.0/logs/phase7_all_tests.log

# 3. Run lint
npm run lint 2>&1 | tee ../docs/releases/v0.10.0/logs/phase7_lint.log

# 4. Run type-check (MANDATORY)
npm run type-check 2>&1 | tee ../docs/releases/v0.10.0/logs/phase7_typecheck.log
```

### 7.5 Commit

```bash
git add web-ui/src/hooks/useJobProgress.ts \
        web-ui/src/hooks/__tests__/useJobProgress.test.ts

git commit -m "feat(web-ui): add useJobProgress hook for WebSocket streaming

- React hook for real-time job progress via WebSocket
- Auto-reconnect on connection loss
- Type-safe progress event handling
- Unit tests with mocked WebSocket

Phase 7 of v0.10.0 implementation."
```

---

## Phase 8: Update JobStatus Component

**Goal:** Modify JobStatus to use WebSocket with HTTP polling fallback.

### 8.1 Files to Modify

| File | Purpose |
|------|---------|
| `web-ui/src/components/JobStatus.tsx` | MODIFY: Use WebSocket with polling fallback |
| `web-ui/src/components/__tests__/JobStatus.test.tsx` | MODIFY: Update tests |

### 8.2 Test Specifications

```typescript
// web-ui/src/components/__tests__/JobStatus.test.tsx

import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { JobStatus } from '../JobStatus';

// Mock useJobProgress hook
vi.mock('../../hooks/useJobProgress', () => ({
  useJobProgress: vi.fn(),
}));

import { useJobProgress } from '../../hooks/useJobProgress';

describe('JobStatus', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows pending state initially', () => {
    vi.mocked(useJobProgress).mockReturnValue({
      progress: null,
      status: 'pending',
      error: null,
      isConnected: false,
    });

    render(<JobStatus jobId="job-123" />);
    
    expect(screen.getByText(/pending/i)).toBeInTheDocument();
  });

  it('shows progress bar when running', () => {
    vi.mocked(useJobProgress).mockReturnValue({
      progress: {
        job_id: 'job-123',
        current_frame: 50,
        total_frames: 100,
        percent: 50,
      },
      status: 'running',
      error: null,
      isConnected: true,
    });

    render(<JobStatus jobId="job-123" />);
    
    expect(screen.getByText(/50%/)).toBeInTheDocument();
    expect(screen.getByText(/Frame 50 \/ 100/)).toBeInTheDocument();
  });

  it('shows WebSocket connection indicator', () => {
    vi.mocked(useJobProgress).mockReturnValue({
      progress: null,
      status: 'pending',
      error: null,
      isConnected: true,
    });

    render(<JobStatus jobId="job-123" />);
    
    // Should show live indicator when connected
    expect(screen.getByTitle(/connected/i)).toBeInTheDocument();
  });

  it('shows completed state', () => {
    vi.mocked(useJobProgress).mockReturnValue({
      progress: null,
      status: 'completed',
      error: null,
      isConnected: true,
    });

    render(<JobStatus jobId="job-123" />);
    
    expect(screen.getByText(/completed/i)).toBeInTheDocument();
  });

  it('shows error state', () => {
    vi.mocked(useJobProgress).mockReturnValue({
      progress: null,
      status: 'failed',
      error: 'Processing failed',
      isConnected: false,
    });

    render(<JobStatus jobId="job-123" />);
    
    expect(screen.getByText(/failed/i)).toBeInTheDocument();
    expect(screen.getByText(/Processing failed/)).toBeInTheDocument();
  });

  it('falls back to polling when WebSocket disconnected', async () => {
    vi.mocked(useJobProgress).mockReturnValue({
      progress: null,
      status: 'pending',
      error: null,
      isConnected: false,  // WebSocket not connected
    });

    render(<JobStatus jobId="job-123" />);
    
    // Should show fallback indicator
    await waitFor(() => {
      expect(screen.getByText(/polling/i)).toBeInTheDocument();
    });
  });
});
```

### 8.3 Implementation Changes

```typescript
// web-ui/src/components/JobStatus.tsx

import React, { useEffect, useState } from 'react';
import { apiClient } from '../api/client';
import { useJobProgress } from '../hooks/useJobProgress';
import { ProgressBar } from './ProgressBar';

interface JobStatusProps {
  jobId: string;
}

type Status = 'pending' | 'running' | 'completed' | 'failed';

export const JobStatus: React.FC<JobStatusProps> = ({ jobId }) => {
  // WebSocket progress (primary)
  const {
    progress: wsProgress,
    status: wsStatus,
    error: wsError,
    isConnected,
  } = useJobProgress(jobId);

  // HTTP polling fallback
  const [pollProgress, setPollProgress] = useState<number | null>(null);
  const [pollStatus, setPollStatus] = useState<Status>('pending');
  const [results, setResults] = useState<Record<string, unknown> | null>(null);
  const [pollError, setPollError] = useState<string | null>(null);

  // Determine which source to use
  const useWebSocket = isConnected && wsStatus !== 'pending';
  const currentProgress = useWebSocket
    ? wsProgress?.percent ?? null
    : pollProgress;
  const currentStatus = useWebSocket ? wsStatus : pollStatus;
  const currentError = wsError || pollError;

  // HTTP polling fallback (when WebSocket not connected)
  useEffect(() => {
    if (isConnected || !jobId) return;

    let timer: number | undefined;

    const poll = async () => {
      try {
        const job = await apiClient.getJob(jobId);
        setPollStatus(job.status as Status);
        setPollProgress(job.progress ?? null);

        if (job.status === 'completed' && job.results) {
          setResults(job.results);
          return; // Stop polling
        }

        if (job.status === 'failed') {
          setPollError(job.error_message || 'Job failed');
          return; // Stop polling
        }

        timer = window.setTimeout(poll, 2000);
      } catch (e) {
        setPollError(e instanceof Error ? e.message : 'Status polling failed');
      }
    };

    poll();

    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [jobId, isConnected]);

  // Render progress info
  const renderProgressInfo = () => {
    if (!wsProgress) return null;

    return (
      <div className="progress-info">
        <span>Frame: {wsProgress.current_frame} / {wsProgress.total_frames}</span>
        {wsProgress.current_tool && (
          <span>Tool: {wsProgress.current_tool}</span>
        )}
        {wsProgress.tools_total && wsProgress.tools_total > 1 && (
          <span>Tool: {wsProgress.tools_completed + 1} of {wsProgress.tools_total}</span>
        )}
      </div>
    );
  };

  return (
    <div className="job-status">
      {/* Connection indicator */}
      <div className="connection-status">
        {isConnected ? (
          <span title="WebSocket connected" className="live-indicator">
            ● Live
          </span>
        ) : (
          <span title="Using HTTP polling" className="polling-indicator">
            ○ Polling
          </span>
        )}
      </div>

      {/* Status display */}
      <div className="status-text">
        Status: {currentStatus}
      </div>

      {/* Progress bar */}
      {currentProgress !== null && (
        <>
          <ProgressBar progress={currentProgress} showPercentage />
          {renderProgressInfo()}
        </>
      )}

      {/* Error display */}
      {currentError && (
        <div className="error-message">
          Error: {currentError}
        </div>
      )}

      {/* Results display */}
      {currentStatus === 'completed' && results && (
        <div className="results">
          <h4>Results</h4>
          <pre>{JSON.stringify(results, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};
```

### 8.4 Verification Commands

```bash
# From ForgeSyte root
cd /home/rogermt/forgesyte/web-ui

# 1. Run component tests
npm run test -- --run src/components/__tests__/JobStatus.test.tsx 2>&1 | tee ../docs/releases/v0.10.0/logs/phase8_tests.log

# 2. Run all tests
npm run test -- --run 2>&1 | tee ../docs/releases/v0.10.0/logs/phase8_all_tests.log

# 3. Run lint
npm run lint 2>&1 | tee ../docs/releases/v0.10.0/logs/phase8_lint.log

# 4. Run type-check (MANDATORY)
npm run type-check 2>&1 | tee ../docs/releases/v0.10.0/logs/phase8_typecheck.log
```

### 8.5 Commit

```bash
git add web-ui/src/components/JobStatus.tsx \
        web-ui/src/components/__tests__/JobStatus.test.tsx

git commit -m "feat(web-ui): add WebSocket progress to JobStatus with polling fallback

- Use useJobProgress hook for real-time updates
- Fallback to HTTP polling when WebSocket disconnected
- Show connection status indicator (Live/Polling)
- Display frame count and tool progress

Phase 8 of v0.10.0 implementation."
```

---

## Phase 9: Integration Tests

**Goal:** Add integration tests for WebSocket progress streaming.

### 9.1 Files to Create

| File | Purpose |
|------|---------|
| `server/tests/integration/test_progress_streaming.py` | NEW: Integration tests |

### 9.2 Test Specifications

```python
# server/tests/integration/test_progress_streaming.py

import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.workers.progress import progress_callback


class TestProgressStreamingIntegration:
    """Integration tests for WebSocket progress streaming."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_end_to_end_progress_streaming(self, client):
        """Test complete flow: connect → receive progress → complete."""
        job_id = "integration-test-job"
        
        with client.websocket_connect(f"/ws/jobs/{job_id}") as ws:
            # 1. Connection established
            ws.send_json({"type": "ping"})
            response = ws.receive_json()
            assert response["type"] == "pong"
            
            # 2. Simulate progress events from worker
            asyncio.run(progress_callback(job_id, 0, 100))
            response = ws.receive_json()
            assert response["percent"] == 0
            
            asyncio.run(progress_callback(job_id, 50, 100))
            response = ws.receive_json()
            assert response["percent"] == 50
            
            asyncio.run(progress_callback(job_id, 100, 100))
            response = ws.receive_json()
            assert response["percent"] == 100
    
    def test_multiple_clients_same_job(self, client):
        """Test multiple clients can subscribe to same job."""
        job_id = "multi-client-job"
        
        with client.websocket_connect(f"/ws/jobs/{job_id}") as ws1:
            with client.websocket_connect(f"/ws/jobs/{job_id}") as ws2:
                # Both should receive progress
                asyncio.run(progress_callback(job_id, 50, 100))
                
                response1 = ws1.receive_json()
                response2 = ws2.receive_json()
                
                assert response1["percent"] == 50
                assert response2["percent"] == 50
    
    def test_client_isolation(self, client):
        """Test clients only receive their own job events."""
        with client.websocket_connect("/ws/jobs/job-A") as wsA:
            with client.websocket_connect("/ws/jobs/job-B") as wsB:
                # Send progress for job-A
                asyncio.run(progress_callback("job-A", 50, 100))
                
                # Only wsA should receive
                responseA = wsA.receive_json()
                assert responseA["job_id"] == "job-A"
                
                # wsB should not receive job-A's progress
                wsB.send_json({"type": "ping"})
                responseB = wsB.receive_json()
                assert responseB["type"] == "pong"  # Not progress
```

### 9.3 Verification Commands

```bash
cd /home/rogermt/forgesyte/server

# Run integration tests
uv run pytest tests/integration/test_progress_streaming.py -v 2>&1 | tee ../docs/releases/v0.10.0/logs/phase9_tests.log

# Run all tests
uv run pytest tests/ -v --tb=short 2>&1 | tee ../docs/releases/v0.10.0/logs/phase9_all_tests.log
```

### 9.4 Commit

```bash
git add server/tests/integration/test_progress_streaming.py

git commit -m "test(server): add integration tests for WebSocket progress streaming

- Test end-to-end progress streaming flow
- Test multiple clients subscribing to same job
- Test client isolation between different jobs

Phase 9 of v0.10.0 implementation."
```

---

## Phase 10: E2E Validation

**Goal:** End-to-end validation of complete v0.10.0 feature.

### 10.1 E2E Test Script

```bash
#!/bin/bash
# docs/releases/v0.10.0/e2e_validation.sh

set -e

echo "=== v0.10.0 E2E Validation ==="
echo ""

# 1. Server health check
echo "1. Checking server health..."
curl -s http://localhost:8000/health | jq .

# 2. Submit video job
echo ""
echo "2. Submitting video job..."
JOB_RESPONSE=$(curl -s -X POST http://localhost:8000/v1/video/submit \
  -F "video=@/path/to/test/video.mp4" \
  -F "plugin_id=yolo-tracker" \
  -F "tool=video_player_tracking")
JOB_ID=$(echo $JOB_RESPONSE | jq -r '.job_id')
echo "Job ID: $JOB_ID"

# 3. Connect to WebSocket and receive progress
echo ""
echo "3. Connecting to WebSocket..."
# Use wscat or similar to test WebSocket
# wscat -c "ws://localhost:8000/ws/jobs/$JOB_ID"

# 4. Wait for completion
echo ""
echo "4. Waiting for completion..."
while true; do
  STATUS=$(curl -s http://localhost:8000/v1/jobs/$JOB_ID | jq -r '.status')
  echo "Status: $STATUS"
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  sleep 2
done

# 5. Get results
echo ""
echo "5. Fetching results..."
curl -s http://localhost:8000/v1/jobs/$JOB_ID | jq '.results'

# 6. Validate JSON schema
echo ""
echo "6. Validating JSON schema..."
curl -s http://localhost:8000/v1/jobs/$JOB_ID | jq '.results' > /tmp/results.json
# Check for NumPy types (should be none)
if grep -q "numpy" /tmp/results.json; then
  echo "FAIL: NumPy types found in output"
  exit 1
else
  echo "PASS: No NumPy types in output"
fi

# Check required fields
if jq -e '.total_frames' /tmp/results.json > /dev/null && \
   jq -e '.frames' /tmp/results.json > /dev/null; then
  echo "PASS: Required fields present"
else
  echo "FAIL: Missing required fields"
  exit 1
fi

echo ""
echo "=== E2E Validation Complete ==="
```

### 10.2 QA Checklist

- [ ] WebSocket connection accepted on `/ws/jobs/{job_id}`
- [ ] Progress events received in real-time
- [ ] Progress bar updates in UI
- [ ] Frame counter displays correctly
- [ ] Completion event triggers results view
- [ ] Final JSON is sanitized (no NumPy types)
- [ ] JSON matches v0.10.0 schema
- [ ] HTTP polling fallback works when WebSocket disconnected
- [ ] Error handling is graceful

### 10.3 Final Verification

```bash
# From ForgeSyte root
cd /home/rogermt/forgesyte

# Full test suite
cd server && uv run pytest tests/ -v 2>&1 | tee ../docs/releases/v0.10.0/logs/phase10_server_tests.log
cd ../web-ui && npm run test -- --run 2>&1 | tee ../docs/releases/v0.10.0/logs/phase10_webui_tests.log

# Pre-commit
cd .. && uv run pre-commit run --all-files 2>&1 | tee docs/releases/v0.10.0/logs/phase10_precommit.log

# Governance
python scripts/scan_execution_violations.py 2>&1 | tee docs/releases/v0.10.0/logs/phase10_governance.log
```

### 10.4 Commit

```bash
git add docs/releases/v0.10.0/e2e_validation.sh \
        docs/releases/v0.10.0/logs/

git commit -m "chore: add E2E validation script and logs for v0.10.0

Phase 10 of v0.10.0 implementation complete."
```

---

## 5. Final Steps

### 5.1 Create Pull Request

```bash
# Push branch
git push origin v0.10.0

# Create PR
gh pr create --base main --head v0.10.0 \
  --title "v0.10.0: Streaming Video Analysis" \
  --body "See DESIGN.md and PLAN.md for full details."
```

### 5.2 Merge After Approval

```bash
# After PR approved
git checkout main
git pull origin main
git merge v0.10.0
git push origin main
git branch -d v0.10.0
```

---

## 6. Rollback Procedure

If any phase fails:

```bash
# Reset to last known good commit
git reset --hard HEAD~1

# Or restore specific files
git checkout HEAD -- path/to/file.py

# Check git log for last good commit
git log --oneline -5

# Reset to specific commit
git reset --hard <commit-hash>
```

---

## 7. Summary of Phases (Commits)

### ForgeSyte Repository (Phases 4-10)

| Phase | Commit Message | Files Changed |
|-------|---------------|---------------|
| 4 | `feat(server): add progress callback module for WebSocket streaming` | `server/app/workers/progress.py`, `server/tests/unit/test_progress.py` |
| 5 | `feat(server): add WebSocket endpoint for job progress streaming` | `server/app/realtime/job_progress_router.py`, `server/tests/api/test_job_progress_ws.py`, `server/app/main.py` |
| 6 | `feat(server): add WebSocket broadcast to worker progress updates` | `server/app/workers/worker.py`, `server/tests/unit/test_worker_progress_broadcast.py` |
| 7 | `feat(web-ui): add useJobProgress hook for WebSocket streaming` | `web-ui/src/hooks/useJobProgress.ts`, `web-ui/src/hooks/__tests__/useJobProgress.test.ts` |
| 8 | `feat(web-ui): update JobStatus for WebSocket progress streaming` | `web-ui/src/components/JobStatus.tsx`, `web-ui/src/components/__tests__/JobStatus.test.tsx` |
| 9 | `test(server): add integration tests for progress streaming` | `server/tests/integration/test_progress_streaming.py` |
| 10 | `chore: add E2E validation script and logs for v0.10.0` | `docs/releases/v0.10.0/e2e_validation.sh`, `docs/releases/v0.10.0/logs/` |

### ForgeSyte-Plugins Repository (Phases 1-3)

| Phase | Commit Message | Files Changed |
|-------|---------------|---------------|
| 1 | `feat(plugin): add JSON sanitizer for NumPy types` | `src/forgesyte_yolo_tracker/utils/json_sanitize.py`, `tests/test_json_sanitize.py` |
| 2 | `fix(plugin): wire JSON sanitizer into video tool outputs` | `src/forgesyte_yolo_tracker/plugin.py`, `tests/test_plugin_output.py` |
| 3 | `feat(plugin): add streaming_video_analysis capability` | `src/forgesyte_yolo_tracker/manifest.json`, `tests/test_manifest.py` |

### Expected Commit History (ForgeSyte)

```bash
# After completing all phases, git log should show:
git log --oneline -7

# Output:
abc1234 chore: add E2E validation script and logs for v0.10.0
def5678 test(server): add integration tests for progress streaming
ghi9012 feat(web-ui): update JobStatus for WebSocket progress streaming
jkl3456 feat(web-ui): add useJobProgress hook for WebSocket streaming
mno7890 feat(server): add WebSocket broadcast to worker progress updates
pqr1234 feat(server): add WebSocket endpoint for job progress streaming
stu5678 feat(server): add progress callback module for WebSocket streaming
```

### Expected Commit History (ForgeSyte-Plugins)

```bash
# After completing all phases, git log should show:
git log --oneline -3

# Output:
xyz1234 feat(plugin): add streaming_video_analysis capability
uvw5678 fix(plugin): wire JSON sanitizer into video tool outputs
rst9012 feat(plugin): add JSON sanitizer for NumPy types
```

---

## 8. References

- **Design Doc:** `./DESIGN.md`
- **GitHub Discussion:** https://github.com/rogermt/forgesyte/discussions/226
- **WebSocket Protocol Spec:** `/docs/design/WEBSOCKET_PROTOCOL_SPEC.md`
- **AGENTS.md:** Development commands and conventions
- **Plugins Plan:** `./PLAN_PLUGINS.md`
