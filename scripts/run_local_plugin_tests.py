#!/usr/bin/env python3
"""Run local plugin loading tests that are skipped in CI.

Usage:
    uv run scripts/run_local_plugin_tests.py
    
These tests require forgesyte-plugins repo at /home/rogermt/forgesyte-plugins
"""

import subprocess
import sys
from pathlib import Path

# Check if forgesyte-plugins exists
plugins_repo = Path("/home/rogermt/forgesyte-plugins")
if not plugins_repo.exists():
    print(f"❌ Error: forgesyte-plugins repo not found at {plugins_repo}")
    print("Clone it first:")
    print(
        "  git clone https://github.com/rogermt/forgesyte-plugins /home/rogermt/forgesyte-plugins"
    )
    sys.exit(1)

print(f"✅ Found forgesyte-plugins at {plugins_repo}")
print()

# Modify test file temporarily to remove skip decorator
test_file = (
    Path(__file__).parent.parent
    / "server"
    / "tests"
    / "integration"
    / "test_local_plugin_loading.py"
)
original_content = test_file.read_text()

# Remove @pytest.mark.skip decorators
modified_content = original_content.replace(
    '@pytest.mark.skip(\n    reason="Requires local forgesyte-plugins repo at /home/rogermt/forgesyte-plugins. "\n    "Not available in CI workflow. Local dev testing only."\n)\n',
    "# LOCALLY ENABLED FOR TESTING (decorator removed)  # ",
)

print("Running local plugin loading tests...")
print()

try:
    # Write modified content
    test_file.write_text(modified_content)

    # Run pytest from server directory
    server_dir = test_file.parent.parent.parent
    result = subprocess.run(
        [
            "uv",
            "run",
            "pytest",
            "tests/integration/test_local_plugin_loading.py",
            "-v",
            "--tb=short",
        ],
        cwd=str(server_dir),
        capture_output=False,
    )

    sys.exit(result.returncode)
finally:
    # Restore original content
    test_file.write_text(original_content)
    print()
    print("✅ Restored test file")
