#!/usr/bin/env bash
set -e

EXPECTED=$(mktemp)
ACTUAL=$(mktemp)

bash scripts/phase6_expected_tests.sh 2>/dev/null | tail -n +2 > "$EXPECTED"
bash scripts/phase6_actual_tests.sh 2>/dev/null | tail -n +2 > "$ACTUAL"

echo "=== Missing Tests (should exist but do not) ==="
comm -23 <(sort "$EXPECTED") <(sort "$ACTUAL") || echo "✓ All expected tests present"

echo ""
echo "=== Unexpected Tests (exist but not in Phase 6 canonical) ==="
comm -13 <(sort "$EXPECTED") <(sort "$ACTUAL") || echo "✓ No unexpected tests"

rm -f "$EXPECTED" "$ACTUAL"
