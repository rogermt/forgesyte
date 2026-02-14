#!/bin/bash
# Demo script for Phase 15 video batch processing
# Demonstrates the YOLO + OCR pipeline on a tiny MP4 file

set -e

# Configuration
SERVER_URL="${SERVER_URL:-http://localhost:8000}"
PIPELINE_ID="${PIPELINE_ID:-yolo_ocr}"
VIDEO_FILE="${VIDEO_FILE:-server/app/tests/fixtures/tiny.mp4}"

echo "=========================================="
echo "Phase 15 Video Batch Demo"
echo "=========================================="
echo "Server URL: $SERVER_URL"
echo "Pipeline ID: $PIPELINE_ID"
echo "Video File: $VIDEO_FILE"
echo ""

# Check if video file exists
if [ ! -f "$VIDEO_FILE" ]; then
    echo "ERROR: Video file not found: $VIDEO_FILE"
    exit 1
fi

# Check if server is running
echo "Checking server status..."
if ! curl -s -f "$SERVER_URL/health" > /dev/null 2>&1; then
    echo "WARNING: Server health check failed. Continuing anyway..."
fi

# Upload and run video processing
echo "Uploading video and running YOLO + OCR pipeline..."
echo ""

RESPONSE=$(curl -s -X POST "$SERVER_URL/video/upload-and-run" \
  -F "file=@$VIDEO_FILE" \
  -F "pipeline_id=$PIPELINE_ID")

# Check if curl succeeded
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to connect to server"
    exit 1
fi

# Pretty-print the response
echo "Response:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"

echo ""
echo "=========================================="
echo "Demo Complete"
echo "=========================================="

# Extract and display first frame result
FIRST_FRAME=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data['results'][0] if data.get('results') else {}, indent=2))" 2>/dev/null || echo "")

if [ -n "$FIRST_FRAME" ]; then
    echo ""
    echo "First Frame Result:"
    echo "$FIRST_FRAME"
fi