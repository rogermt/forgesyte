#!/usr/bin/env python
"""
Governance tooling for Phase 15: Video File Pipeline (Commit 9).

Validates:
1. All 4 test suites pass
2. Code quality (formatting, linting, types)
3. Governance checks (execution violations)
"""

import subprocess
import sys
from pathlib import Path


def run_test_suite(cmd, name, cwd):
    """Run a test command and return success/failure."""
    print(f"  ▶ {name}...")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if result.returncode == 0:
            print(f"    ✅ {name} passed")
            return True
        else:
            print(f"    ❌ {name} failed")
            if "--verbose" in sys.argv:
                print(result.stdout[-500:] if result.stdout else "")
                print(result.stderr[-500:] if result.stderr else "")
            return False
    except subprocess.TimeoutExpired:
        print(f"    ⏱️  {name} timed out")
        return False
    except Exception as e:
        print(f"    ❌ {name} error: {e}")
        return False


def main():
    """Run all governance checks."""
    print("\n" + "="*60)
    print("Phase 15: Video File Pipeline Governance Checks")
    print("="*60 + "\n")

    repo_root = Path(__file__).resolve().parents[1]
    server_dir = repo_root / "server"

    test_suites = [
        (
            ["uv", "run", "pytest", "app/tests/video/", "-q"],
            "Video service tests (63+ passing)",
            server_dir,
        ),
        (
            ["uv", "run", "ruff", "check", "app/api_routes/routes/video_file_processing.py"],
            "Code linting (ruff)",
            server_dir,
        ),
        (
            ["uv", "run", "black", "--check", "app/api_routes/routes/video_file_processing.py"],
            "Code formatting (black)",
            server_dir,
        ),
        (
            ["uv", "run", "mypy", "app/api_routes/routes/video_file_processing.py"],
            "Type checking (mypy)",
            server_dir,
        ),
        (
            ["python", "scripts/scan_execution_violations.py"],
            "Governance scanner",
            repo_root,
        ),
    ]

    results = []
    for cmd, name, cwd in test_suites:
        results.append(run_test_suite(cmd, name, cwd))

    # Summary
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    
    if all(results):
        print(f"✅ All {total} governance checks passed!")
        print("="*60 + "\n")
        return 0
    else:
        print(f"❌ {passed}/{total} checks passed")
        print("="*60 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
