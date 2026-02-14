#!/usr/bin/env python3
"""Vocabulary Scanner Tool.

Validates that job-processing code does not contain forbidden vocabulary.

Exit Codes:
- 0: No violations found
- 1: Violations found
"""

import sys
from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: Path) -> dict[str, Any]:
    """Load scanner configuration from YAML file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def normalize_term(term: str, case_sensitive: bool = False) -> str:
    """Normalize term for comparison."""
    return term if case_sensitive else term.lower()


def scan_file(
    filepath: Path,
    forbidden_terms: list[str],
    case_sensitive: bool = False,
    context_lines: int = 2,
) -> list[dict[str, Any]]:
    """Scan a file for forbidden vocabulary.

    Returns list of violations with file, line number, term, and context.
    """
    violations = []

    try:
        content = filepath.read_text()
    except (UnicodeDecodeError, PermissionError):
        return violations

    lines = content.split("\n")

    for line_no, line in enumerate(lines, 1):
        line_normalized = normalize_term(line, case_sensitive)

        for term in forbidden_terms:
            term_normalized = normalize_term(term, case_sensitive)

            if term_normalized in line_normalized:
                # Extract context
                start = max(0, line_no - context_lines - 1)
                end = min(len(lines), line_no + context_lines)
                context = lines[start:end]

                violations.append(
                    {
                        "file": str(filepath),
                        "line": line_no,
                        "term": term,
                        "line_content": line.strip(),
                        "context": context,
                    }
                )

    return violations


def should_scan_file(
    filepath: Path,
    include_patterns: list[str],
    exclude_dirs: list[str],
) -> bool:
    """Determine if file should be scanned."""
    # Check exclude directories
    for exclude_dir in exclude_dirs:
        if exclude_dir in filepath.parts:
            return False

    # Check include patterns
    for pattern in include_patterns:
        if filepath.match(pattern):
            return True

    return False


def scan_directory(
    root_dir: Path,
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Recursively scan directory for violations."""
    all_violations = []

    forbidden_terms = config.get("forbidden_terms", [])
    scan_dirs = config.get("scan_directories", ["app"])
    exclude_dirs = config.get("exclude_directories", [])
    include_patterns = config.get("include_patterns", ["*.py"])
    case_sensitive = config.get("case_sensitive", False)
    context_lines = config.get("reporting", {}).get("context_lines", 2)

    for scan_dir in scan_dirs:
        scan_path = root_dir / scan_dir

        if not scan_path.exists():
            continue

        if scan_path.is_file():
            files_to_scan = [scan_path]
        else:
            files_to_scan = list(scan_path.rglob("*.py"))

        for filepath in files_to_scan:
            if not should_scan_file(filepath, include_patterns, exclude_dirs):
                continue

            violations = scan_file(
                filepath,
                forbidden_terms,
                case_sensitive,
                context_lines,
            )
            all_violations.extend(violations)

    return all_violations


def format_violation(violation: dict[str, Any]) -> str:
    """Format a violation for display."""
    filepath = violation["file"]
    line_no = violation["line"]
    term = violation["term"]
    line_content = violation["line_content"]
    context = violation["context"]

    output = f"\n{filepath}:{line_no}\n"
    output += f"  Forbidden term: '{term}'\n"
    output += f"  Line content: {line_content}\n"

    if context:
        output += "  Context:\n"
        for ctx_line in context:
            output += f"    {ctx_line}\n"

    return output


def main():
    """Run vocabulary scanner."""
    # Determine server root directory
    script_dir = Path(__file__).parent
    server_root = script_dir.parent

    config_path = script_dir / "vocabulary_scanner_config.yaml"

    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}", file=sys.stderr)
        return 1

    # Load configuration
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"ERROR: Failed to load config: {e}", file=sys.stderr)
        return 1

    # Scan for violations
    violations = scan_directory(server_root, config)

    if not violations:
        print("✓ Vocabulary Scanner: CLEAN (no violations found)")
        return 0

    # Report violations
    print(f"✗ Vocabulary Scanner: VIOLATIONS FOUND ({len(violations)} total)")
    print("\nViolations:")

    for violation in violations:
        print(format_violation(violation))

    print("\nFix violations before committing or merging to main.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
