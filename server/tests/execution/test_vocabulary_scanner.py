"""Test Vocabulary Scanner Tool.

Tests verify:
- Forbidden vocabulary is not present in functional code
- Vocabulary scanner tool exists and is executable
- Scanner configuration file has required terms
"""

from pathlib import Path


class TestVocabularyScanner:
    """Tests for vocabulary scanner tool."""

    def test_no_forbidden_vocabulary_in_functional_code(self):
        """TEST-CHANGE: Assert forbidden vocabulary not in job-processing code.

        Scanned vocabulary:
        - gpu_schedule
        - gpu_worker
        - distributed

        Note: These are Phase 17+ concepts that should not enter Phase 16 code.
        websocket, streaming, sse, real_time are pre-Phase-16 and allowed.
        """
        forbidden_terms = [
            "gpu_schedule",
            "gpu_worker",
            "distributed",
        ]

        # Job processing code directories
        scan_paths = [
            Path(
                "/home/rogermt/forgesyte/server/app/api_routes/routes/video_submit.py"
            ),
            Path("/home/rogermt/forgesyte/server/app/api_routes/routes/job_status.py"),
            Path("/home/rogermt/forgesyte/server/app/api_routes/routes/job_results.py"),
            Path("/home/rogermt/forgesyte/server/app/services/queue"),
            Path("/home/rogermt/forgesyte/server/app/services/storage"),
            Path(
                "/home/rogermt/forgesyte/server/app/services/job_management_service.py"
            ),
            Path("/home/rogermt/forgesyte/server/app/workers"),
        ]

        violations = []

        for scan_path in scan_paths:
            if not scan_path.exists():
                continue

            # Get all Python files
            if scan_path.is_file():
                files = [scan_path]
            else:
                files = list(scan_path.rglob("*.py"))

            for filepath in files:
                try:
                    content = filepath.read_text()
                    for term in forbidden_terms:
                        # Case-insensitive search
                        if term.lower() in content.lower():
                            # Count occurrences
                            count = content.lower().count(term.lower())
                            violations.append(
                                f"{filepath.relative_to('/home/rogermt/forgesyte')}: "
                                f"'{term}' found {count} times"
                            )
                except Exception:
                    # Skip files that can't be read
                    pass

        assert (
            not violations
        ), "Forbidden vocabulary found in job-processing code:\n" + "\n".join(
            violations
        )

    def test_scanner_tool_exists(self):
        """TEST-CHANGE: Assert vocabulary scanner tool is present and executable."""
        scanner_path = Path(
            "/home/rogermt/forgesyte/server/tools/vocabulary_scanner.py"
        )

        # Verify scanner exists
        assert scanner_path.exists(), f"Vocabulary scanner not found at {scanner_path}"

        # Verify it's not empty
        assert scanner_path.stat().st_size > 0, "Scanner file is empty"

    def test_scanner_config_exists(self):
        """TEST-CHANGE: Assert scanner config file exists with forbidden terms.

        Config should:
        - Be a YAML file at server/tools/vocabulary_scanner_config.yaml
        - List forbidden vocabulary
        - Be readable
        """
        config_path = Path(
            "/home/rogermt/forgesyte/server/tools/vocabulary_scanner_config.yaml"
        )

        # Verify config exists
        assert config_path.exists(), f"Scanner config not found at {config_path}"

        # Verify it's not empty
        assert config_path.stat().st_size > 0, "Config file is empty"

        # Verify required forbidden terms are in config
        content = config_path.read_text()
        required_terms = [
            "gpu_schedule",
            "gpu_worker",
            "distributed",
        ]

        for term in required_terms:
            assert term in content, f"Required term '{term}' not in config"
