#!/usr/bin/env bash
set -e

echo "=== Actual Test Count (via npm test) ==="

cd web-ui
npm test -- --run --json --outputFile=/tmp/jest.json >/dev/null 2>&1

jq '.numTotalTests' /tmp/jest.json 2>/dev/null || echo "Error: Could not get test count"
