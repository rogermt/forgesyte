#!/bin/bash
# Run local plugin loading tests (actually runs them, not just checks they're skipped)
# Only use this when forgesyte-plugins repo is available locally

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

# Create temporary conftest to remove skip decorators at runtime
CONFTEST_PATH="tests/conftest_local.py"
cat > "$CONFTEST_PATH" << 'EOF'
"""Conftest for local plugin testing - removes skip markers."""
import pytest
import sys

# Add parent to path so we can import pytest module
sys.path.insert(0, str(sys.modules['pytest'].__path__[0]))

# Hook to run skipped tests
def pytest_runtest_setup(item):
    """Remove skip markers for local testing."""
    # Check if test is in local_plugin_loading module
    if "test_local_plugin_loading" in str(item.fspath):
        # Remove skip markers
        item.iter_markers = lambda name="skip": iter([])
        # Prevent marking as skipped
        for mark in item.iter_markers():
            if mark.name == "skip":
                item.pop_marker(mark.name)
EOF

echo "Running local plugin loading tests..."
echo ""

# Run tests with temporary conftest
uv run pytest \
  tests/integration/test_local_plugin_loading.py \
  -v \
  --tb=short \
  -p no:cacheprovider

# Clean up
rm -f "$CONFTEST_PATH"

echo ""
echo "✅ Local plugin loading tests completed"
