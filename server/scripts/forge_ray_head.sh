#!/bin/bash
# forge-ray-head.sh - Start a Ray head node for ForgeSyte
#
# Usage:
#   ./forge-ray-head.sh [options]
#
# Options:
#   --port PORT          Ray GCS server port (default: 6379)
#   --dashboard-port PORT Dashboard port (default: 8265)
#   --help               Show this help message
#
# Environment variables:
#   RAY_HEAD_PORT        Override default GCS port
#   RAY_DASHBOARD_PORT   Override default dashboard port

set -e

# Default values
GCS_PORT="${RAY_HEAD_PORT:-6379}"
DASHBOARD_PORT="${RAY_DASHBOARD_PORT:-8265}"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            GCS_PORT="$2"
            shift 2
            ;;
        --dashboard-port)
            DASHBOARD_PORT="$2"
            shift 2
            ;;
        --help|-h)
            echo "ForgeSyte Ray Head Node Starter"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --port PORT          Ray GCS server port (default: $GCS_PORT)"
            echo "  --dashboard-port PORT Dashboard port (default: $DASHBOARD_PORT)"
            echo "  --help               Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  RAY_HEAD_PORT        Override default GCS port"
            echo "  RAY_DASHBOARD_PORT   Override default dashboard port"
            echo ""
            echo "After starting, workers can connect with:"
            echo "  ray start --address='<HEAD_IP>:$GCS_PORT'"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "============================================================"
echo "ForgeSyte Ray Head Node"
echo "============================================================"
echo ""
echo "Starting Ray head with:"
echo "  GCS Port: $GCS_PORT"
echo "  Dashboard Port: $DASHBOARD_PORT"
echo ""

# Start Ray head
ray start --head \
    --port="$GCS_PORT" \
    --dashboard-port="$DASHBOARD_PORT" \
    --dashboard-host=0.0.0.0

echo ""
echo "============================================================"
echo "Ray Head Started Successfully!"
echo "============================================================"
echo ""
echo "Dashboard: http://localhost:$DASHBOARD_PORT"
echo ""
echo "Workers can connect with:"
echo "  ray start --address='<HEAD_IP>:$GCS_PORT'"
echo ""
echo "For ForgeSyte, set environment variable:"
echo "  export RAY_ADDRESS='ray://localhost:10001'"
echo ""
echo "To stop the Ray cluster:"
echo "  ray stop"
