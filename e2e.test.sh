#!/bin/bash

# ForgeSyte E2E Test Script
# Starts server and runs WebUI integration tests against it

set -e

# Configuration
SERVER_PORT=8000
WEB_UI_PORT=3000
SERVER_DIR="./server"
WEB_UI_DIR="./web-ui"
LOG_DIR="./logs"

mkdir -p $LOG_DIR

echo "🚀 Starting E2E Test Suite..."

# 1. Kill any existing processes on ports
echo "🧹 Cleaning up existing processes..."
fuser -k $SERVER_PORT/tcp || true
fuser -k $WEB_UI_PORT/tcp || true

# 2. Start Server
echo "Backend: Starting server..."
cd $SERVER_DIR
uv run uvicorn app.main:app --host 127.0.0.1 --port $SERVER_PORT > ../$LOG_DIR/server.log 2>&1 &
SERVER_PID=$!
cd ..

# 3. Wait for Server Health Check
echo "Backend: Waiting for health check..."
MAX_RETRIES=30
RETRY_COUNT=0
until curl -s http://127.0.0.1:$SERVER_PORT/v1/health | grep -q "healthy"; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ Error: Server failed to start or health check timed out"
        kill $SERVER_PID
        exit 1
    fi
    sleep 1
done
echo "✅ Backend: Healthy"

# 3b. Test WebSocket endpoint exists
echo "Backend: Testing WebSocket endpoint..."
cd $SERVER_DIR
WS_TEST_RESULT=$(uv run pytest tests/websocket/test_websocket_integration.py::TestWebSocketEndpointExists::test_websocket_endpoint_exists -v 2>&1)
if echo "$WS_TEST_RESULT" | grep -q "PASSED"; then
    echo "✅ Backend: WebSocket endpoint verified"
else
    echo "❌ Error: WebSocket endpoint test failed"
    echo "$WS_TEST_RESULT"
    kill $SERVER_PID
    exit 1
fi
cd ..

# 4. Run WebUI Integration Tests against REAL server
echo "Frontend: Running integration tests..."
cd $WEB_UI_DIR
# Point both REST API and WebSocket to the real server
VITE_API_URL="http://127.0.0.1:$SERVER_PORT/v1" \
VITE_WS_BACKEND_URL="ws://127.0.0.1:$SERVER_PORT" \
npm run test:integration -- --run
TEST_EXIT_CODE=$?
cd ..

# 5. Cleanup
echo "🧹 Cleaning up..."
kill $SERVER_PID

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✨ E2E Tests PASSED"
    exit 0
else
    echo "❌ E2E Tests FAILED (Exit Code: $TEST_EXIT_CODE)"
    exit $TEST_EXIT_CODE
fi
