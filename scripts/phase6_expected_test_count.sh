#!/usr/bin/env bash
set -e

echo "=== Expected Phase 6 Test Count ==="

bash scripts/phase6_expected_tests.sh 2>/dev/null | tail -n +2 | wc -l
