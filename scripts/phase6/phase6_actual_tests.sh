#!/usr/bin/env bash
set -e

echo "=== Actual Test Files in Repo ==="
find web-ui/src -type f -name "*.test.ts*" | sort
