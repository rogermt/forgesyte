# Issue: WebSocket Error Message Appears Unnecessarily on Successful Connections

## Description
The WebSocket error message "WebSocket connection error. Unable to connect to ws://localhost:8000/v1/stream?plugin=motion_detector. Check if backend server is running on port 8000." appears before every successful connection, even when the connection is actually successful.

## Expected Behavior
The error message should only appear when there's an actual connection failure, not on successful connections.

## Actual Behavior
The error message appears before every successful connection, causing confusion for users.

## Root Cause
In `/web-ui/src/hooks/useWebSocket.ts`, the error state is set in the `onerror` and `onclose` handlers but is not cleared in the `onopen` handler when a successful connection is established. This causes any previous error message to persist in the UI even after a successful connection is made.

## Location
File: `/web-ui/src/hooks/useWebSocket.ts`
Line: ~97 (error message generation and state management)

## Suggested Fix
Clear the error state in the `onopen` handler when a successful connection is established to prevent showing stale error messages on successful connections.