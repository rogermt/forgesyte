#!/bin/bash
# forge-ray-worker.sh - Connect a Ray worker node to a ForgeSyte Ray head
#
# Usage:
#   ./forge-ray-worker.sh --address <HEAD_ADDRESS> [options]
#
# Options:
#   --address ADDRESS     Ray head node address (required)
#                         Format: <host>:<port> (e.g., 192.168.1.100:6379)
#   --num-gpus N          Number of GPUs to expose (default: auto-detect)
#   --num-cpus N          Number of CPUs to use (default: auto-detect)
#   --help                Show this help message
#
# Environment variables:
#   RAY_ADDRESS          Ray head address (alternative to --address)
#   CUDA_VISIBLE_DEVICES GPUs to use (e.g., "0,1,2,3")

set -e

# Default values
HEAD_ADDRESS="${RAY_ADDRESS:-}"
NUM_GPUS=""
NUM_CPUS=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --address)
            HEAD_ADDRESS="$2"
            shift 2
            ;;
        --num-gpus)
            NUM_GPUS="$2"
            shift 2
            ;;
        --num-cpus)
            NUM_CPUS="$2"
            shift 2
            ;;
        --help|-h)
            echo "ForgeSyte Ray Worker Node Starter"
            echo ""
            echo "Usage: $0 --address <HEAD_ADDRESS> [options]"
            echo ""
            echo "Options:"
            echo "  --address ADDRESS     Ray head node address (required)"
            echo "                        Format: <host>:<port> (e.g., 192.168.1.100:6379)"
            echo "  --num-gpus N          Number of GPUs to expose (default: auto-detect)"
            echo "  --num-cpus N          Number of CPUs to use (default: auto-detect)"
            echo "  --help                Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  RAY_ADDRESS           Ray head address (alternative to --address)"
            echo "  CUDA_VISIBLE_DEVICES  GPUs to use (e.g., '0,1,2,3')"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$HEAD_ADDRESS" ]]; then
    echo "Error: --address is required"
    echo "Use --help for usage information"
    exit 1
fi

echo "============================================================"
echo "ForgeSyte Ray Worker Node"
echo "============================================================"
echo ""
echo "Connecting to Ray head at: $HEAD_ADDRESS"

# Build Ray start command
RAY_CMD="ray start --address='$HEAD_ADDRESS'"

if [[ -n "$NUM_GPUS" ]]; then
    RAY_CMD="$RAY_CMD --num-gpus=$NUM_GPUS"
    echo "GPUs: $NUM_GPUS"
else
    echo "GPUs: auto-detect"
fi

if [[ -n "$NUM_CPUS" ]]; then
    RAY_CMD="$RAY_CMD --num-cpus=$NUM_CPUS"
    echo "CPUs: $NUM_CPUS"
else
    echo "CPUs: auto-detect"
fi

echo ""

# Start Ray worker
eval $RAY_CMD

echo ""
echo "============================================================"
echo "Ray Worker Connected Successfully!"
echo "============================================================"
echo ""
echo "Connected to: $HEAD_ADDRESS"
echo ""
echo "To stop this worker:"
echo "  ray stop"
