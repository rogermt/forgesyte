#!/usr/bin/env python3
"""Governance validator for Phase 15 video batch pipeline.

Enforces:
1. No forbidden vocabulary (Phase 16+ concepts)
2. No phase-named files in functional directories (code isolation)
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

import yaml  # type: ignore[import-untyped]


def load_forbidden_patterns() -> List[Tuple[str, str]]:
    """Load forbidden vocabulary patterns from YAML."""
    vocab_file = Path(__file__).parent / "forbidden_vocabulary.yaml"
    if not vocab_file.exists():
        print(f"ERROR: {vocab_file} not found")
        sys.exit(1)

    with open(vocab_file) as f:
        data = yaml.safe_load(f)

    patterns = []
    for item in data.get("patterns", []):
        pattern = item.get("pattern")
        reason = item.get("reason")
        if pattern and reason:
            patterns.append((pattern, reason))

    return patterns


def scan_file_for_violations(
    filepath: Path, patterns: List[Tuple[str, str]]
) -> List[str]:
    """Scan single file for forbidden patterns."""
    violations = []
    try:
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, 1):
                for pattern, reason in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        violations.append(
                            f"{filepath}:{line_no}: {reason}\n    {line.strip()}"
                        )
    except Exception:
        # Skip binary files, permission errors, etc.
        pass

    return violations


def scan_video_functional_files(patterns: List[Tuple[str, str]]) -> List[str]:
    """Scan video pipeline functional files for forbidden terms."""
    violations = []
    base = Path("server/app")

    # Video-related functional files
    scan_patterns = [
        "services/video_file_pipeline_service.py",
        "api_routes/routes/video_file_processing.py",
        "tests/video/**/*.py",
    ]

    for pattern in scan_patterns:
        for filepath in base.glob(pattern):
            if filepath.is_file():
                violations.extend(scan_file_for_violations(filepath, patterns))

    return violations


def scan_phase_named_files() -> List[str]:
    """Scan for phase-named files in functional directories."""
    violations = []
    phase_patterns = [r"phase_?15", r"phase_?16", r"phase_?17"]
    scan_dirs = ["server/app", "server/tools"]

    for scan_dir in scan_dirs:
        base = Path(scan_dir)
        if not base.exists():
            continue

        for filepath in base.rglob("*.py"):
            # Skip tests and docs
            if "tests" in filepath.parts or "docs" in filepath.parts:
                continue

            for phase_pattern in phase_patterns:
                if re.search(phase_pattern, filepath.name, re.IGNORECASE):
                    violations.append(
                        f"{filepath}: Contains phase name in filename "
                        f"(should be removed or moved to docs/design/)"
                    )

    return violations


def main() -> int:
    """Run all validators."""
    violations = []
    patterns = load_forbidden_patterns()

    # Check 1: Forbidden vocabulary in video files
    video_violations = scan_video_functional_files(patterns)
    if video_violations:
        print("❌ FORBIDDEN VOCABULARY VIOLATIONS:")
        for violation in video_violations:
            print(f"  {violation}")
        violations.extend(video_violations)

    # Check 2: Phase-named files in functional directories
    phase_violations = scan_phase_named_files()
    if phase_violations:
        print("❌ PHASE-NAMED FILE VIOLATIONS:")
        for violation in phase_violations:
            print(f"  {violation}")
        violations.extend(phase_violations)

    if violations:
        print(f"\n❌ Validation FAILED: {len(violations)} violation(s)")
        return 1

    print("✅ Validation PASSED: No forbidden vocabulary or phase names found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
