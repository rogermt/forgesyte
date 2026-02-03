#!/usr/bin/env bash
set -e

echo "=== Detecting Partial Test Runs ==="

cd web-ui

TEST_FILES=$(npm test -- --listTests 2>/dev/null | grep -c "test\." || echo "0")
EXPECTED_FILES=$(bash ../scripts/phase6_expected_test_count.sh 2>/dev/null | tail -1)

echo "Expected test files: $EXPECTED_FILES"
echo "Actual test files:   $TEST_FILES"

if [ "$TEST_FILES" -lt "$EXPECTED_FILES" ]; then
    echo "⚠️  WARNING: Only running $TEST_FILES of $EXPECTED_FILES tests!"
    echo "This indicates a PARTIAL RUN (dev may have modified test execution)."
else
    echo "✓ Full test suite is being executed"
fi
