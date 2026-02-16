"""Phase 17: WebSocket endpoint for real-time video streaming.

Provides the /ws/video/stream WebSocket endpoint for real-time frame-by-frame
inference through Phase 15 DAG pipelines.

This endpoint:
- Accepts binary JPEG frames
- Validates frames
- Runs Phase 15 pipeline per frame
- Streams results back to client
- Implements backpressure (drop frames / slow-down signals)
- No persistence (ephemeral sessions)

Author: Roger
Phase: 17
"""

import logging
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.services.streaming.session_manager import SessionManager
from app.services.streaming.frame_validator import validate_jpeg, FrameValidationError
from app.services.video_file_pipeline_service import VideoFilePipelineService

router = APIRouter()
logger = logging.getLogger("streaming")


@router.websocket("/ws/video/stream")
async def video_stream(
    websocket: WebSocket,
    pipeline_id: Optional[str] = Query(None),
) -> None:
    """Real-time video streaming WebSocket endpoint.

    Args:
        websocket: The WebSocket connection.
        pipeline_id: ID of the pipeline to use for inference (required).

    Raises:
        WebSocketDisconnect: If client disconnects.
    """
    await websocket.accept()

    # Validate pipeline_id
    if pipeline_id is None:
        await websocket.send_json({
            "error": "invalid_pipeline",
            "detail": "pipeline_id query parameter is required"
        })
        await websocket.close()
        return

    # Create SessionManager for this connection
    session = SessionManager(pipeline_id=pipeline_id)
    websocket.state.session = session

    logger.info(
        "stream_connect",
        extra={
            "event_type": "stream_connect",
            "session_id": session.session_id,
            "pipeline_id": pipeline_id,
        }
    )

    try:
        # Keep connection open and process frames
        while True:
            # Receive message (can be bytes or text)
            message = await websocket.receive()

            # Check message type
            if "bytes" in message:
                # Binary frame received
                frame_bytes = message["bytes"]

                # Validate frame
                try:
                    validate_jpeg(frame_bytes)
                except FrameValidationError as e:
                    # Send error and close connection
                    await websocket.send_json({
                        "error": e.code,
                        "detail": e.detail
                    })
                    await websocket.close()
                    return

                # Increment frame index
                session.increment_frame()

                # Pipeline execution will be added in Commit 7
                # For now, just accept the frame

            elif "text" in message:
                # Text message received - reject with error
                await websocket.send_json({
                    "error": "invalid_message",
                    "detail": "Expected binary frame payload, received text message"
                })
                await websocket.close()
                return
            else:
                # Unknown message type
                await websocket.send_json({
                    "error": "invalid_message",
                    "detail": "Expected binary frame payload"
                })
                await websocket.close()
                return

    except WebSocketDisconnect:
        logger.info(
            "stream_disconnect",
            extra={
                "event_type": "stream_disconnect",
                "session_id": session.session_id,
                "pipeline_id": pipeline_id,
            }
        )
    except Exception as e:
        # Check if this is a disconnect-related error
        if "disconnect" in str(e).lower() or "Cannot call \"receive\"" in str(e):
            # This is a disconnect, log as info
            logger.info(
                "stream_disconnect",
                extra={
                    "event_type": "stream_disconnect",
                    "session_id": session.session_id,
                    "pipeline_id": pipeline_id,
                }
            )
        else:
            # Other errors
            logger.error(
                "stream_error",
                extra={
                    "event_type": "stream_error",
                    "session_id": session.session_id,
                    "pipeline_id": pipeline_id,
                    "error": str(e),
                }
            )
            await websocket.close()
    finally:
        # Log disconnect if not already logged
        # This ensures disconnect is logged even if WebSocketDisconnect wasn't raised
        logger.info(
            "stream_disconnect",
            extra={
                "event_type": "stream_disconnect",
                "session_id": session.session_id,
                "pipeline_id": pipeline_id,
            }
        )
        # Destroy session on disconnect
        websocket.state.session = None