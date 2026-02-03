#!/usr/bin/env bash
set -e

echo "=== Detecting Skipped/Only Tests ==="

SKIPPED=$(grep -R "it\.skip\|describe\.skip\|test\.skip\|it\.only\|describe\.only\|test\.only\|xit\|xdescribe" web-ui/src -n 2>/dev/null || true)

if [ -z "$SKIPPED" ]; then
    echo "✓ No skipped or .only tests found"
else
    echo "⚠️  FOUND SKIPPED/ONLY TESTS:"
    echo "$SKIPPED"
fi
