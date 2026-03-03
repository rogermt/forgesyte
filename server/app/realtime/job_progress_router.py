"""WebSocket endpoint for job progress streaming.

v0.10.0: Real-time progress updates for video jobs.

This module provides:
- /ws/jobs/{job_id}: WebSocket endpoint for job progress subscription
"""

import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.websocket_manager import ws_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/v1/ws/jobs/{job_id}")
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
        "percent": 42,
        "current_tool": "example-tool",  // optional
        "tools_total": 2,                 // optional
        "tools_completed": 1              // optional
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
