"""Test Phase 16 Governance Enforcement - FIXED with relative paths"""
from pathlib import Path

class TestPhase16Governance:
    def test_no_forbidden_vocabulary_in_functional_code(self):
        forbidden_terms = ["gpu_schedule", "gpu_worker", "distributed"]
        test_file = Path(__file__)
        server_root = test_file.parent.parent.parent
        
        scan_paths = [
            server_root / "app/api_routes/routes/video_submit.py",
            server_root / "app/api_routes/routes/job_status.py",
            server_root / "app/api_routes/routes/job_results.py",
            server_root / "app/services/queue",
            server_root / "app/services/storage",
            server_root / "app/services/job_management_service.py",
            server_root / "app/workers",
        ]
        violations = []
        for scan_path in scan_paths:
            if not scan_path.exists():
                continue
            if scan_path.is_file():
                files = [scan_path]
            else:
                files = list(scan_path.rglob("*.py"))
            for filepath in files:
                try:
                    content = filepath.read_text()
                    for term in forbidden_terms:
                        if term.lower() in content.lower():
                            count = content.lower().count(term.lower())
                            violations.append(f"{filepath.relative_to(server_root)}: '{term}' found {count} times")
                except Exception:
                    pass
        assert not violations, "Forbidden vocabulary found in Phase 16 functional code:\n" + "\n".join(violations)

    def test_governance_scanner_runs(self):
        test_file = Path(__file__)
        server_root = test_file.parent.parent.parent
        scanner_path = server_root / "tools/vocabulary_scanner.py"
        assert scanner_path.exists(), f"Governance scanner not found at {scanner_path}"
        assert scanner_path.stat().st_size > 0, "Scanner file is empty"

    def test_governance_config_exists(self):
        test_file = Path(__file__)
        server_root = test_file.parent.parent.parent
        config_path = server_root / "tools/forbidden_vocabulary.yaml"
        assert config_path.exists(), f"Governance config not found at {config_path}"
        assert config_path.stat().st_size > 0, "Config file is empty"
        content = config_path.read_text()
        required_terms = ["gpu_schedule", "gpu_worker", "distributed"]
        for term in required_terms:
            assert term in content, f"Required term '{term}' not in config"
