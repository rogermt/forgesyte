#!/bin/bash
# Run local plugin loading tests that are skipped in CI
# These tests require forgesyte-plugins repo at /home/rogermt/forgesyte-plugins

set -e

PLUGINS_REPO="/home/rogermt/forgesyte-plugins"

# Check if forgesyte-plugins repo exists
if [ ! -d "$PLUGINS_REPO" ]; then
    echo "❌ Error: forgesyte-plugins repo not found at $PLUGINS_REPO"
    echo "Clone it first:"
    echo "  git clone https://github.com/rogermt/forgesyte-plugins /home/rogermt/forgesyte-plugins"
    exit 1
fi

echo "✅ Found forgesyte-plugins at $PLUGINS_REPO"
echo ""

# Change to server directory
cd "$(dirname "$0")/../server"

# Run tests with -m "" to include skipped tests
echo "Running local plugin loading tests..."
uv run pytest tests/integration/test_local_plugin_loading.py -v --tb=short

echo ""
echo "✅ Local plugin loading tests completed"
