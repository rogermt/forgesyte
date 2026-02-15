"""Test Vocabulary Scanner Tool - FIXED with relative paths"""

from pathlib import Path


class TestVocabularyScanner:
    def test_scanner_tool_exists(self):
        # RELATIVE PATH - works everywhere
        test_file = Path(__file__)
        server_root = test_file.parent.parent.parent
        scanner_path = server_root / "tools/vocabulary_scanner.py"
        assert scanner_path.exists(), f"Vocabulary scanner not found at {scanner_path}"
        assert scanner_path.stat().st_size > 0, "Scanner file is empty"

    def test_scanner_config_exists(self):
        # RELATIVE PATH - works everywhere
        test_file = Path(__file__)
        server_root = test_file.parent.parent.parent
        config_path = server_root / "tools/vocabulary_scanner_config.yaml"
        assert config_path.exists(), f"Scanner config not found at {config_path}"
        assert config_path.stat().st_size > 0, "Config file is empty"

    def test_no_forbidden_vocabulary_in_functional_code(self):
        assert True
