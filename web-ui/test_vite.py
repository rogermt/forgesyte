"""Tests for Vite configuration and index.html."""

from pathlib import Path


def test_vite_config_exists():
    """Test that vite.config.ts exists."""
    vite_config = Path(__file__).parent / "vite.config.ts"
    assert vite_config.exists(), "vite.config.ts does not exist"


def test_vite_config_has_react():
    """Test that vite.config.ts has React plugin."""
    vite_config = Path(__file__).parent / "vite.config.ts"
    content = vite_config.read_text()
    assert "react" in content.lower(), "vite.config should import React plugin"
    assert "defineConfig" in content, "vite.config should use defineConfig"


def test_vite_config_has_proxy():
    """Test that vite.config.ts has proxy configuration."""
    vite_config = Path(__file__).parent / "vite.config.ts"
    content = vite_config.read_text()
    assert "proxy" in content, "vite.config should have proxy config"
    assert "/v1" in content, "proxy should target /v1 API endpoint"


def test_index_html_exists():
    """Test that index.html exists."""
    index = Path(__file__).parent / "index.html"
    assert index.exists(), "index.html does not exist"


def test_index_html_is_valid():
    """Test that index.html has valid structure."""
    index = Path(__file__).parent / "index.html"
    content = index.read_text()
    assert content.strip().startswith("<!DOCTYPE html>"), "Should be HTML5 document"
    assert "<html" in content, "Should have html tag"
    assert "</html>" in content, "Should have closing html tag"


def test_index_html_has_app_root():
    """Test that index.html has div#app for React."""
    index = Path(__file__).parent / "index.html"
    content = index.read_text()
    assert (
        'id="app"' in content or "id='app'" in content
    ), "Should have div#app for React"


def test_index_html_has_script():
    """Test that index.html references main.tsx."""
    index = Path(__file__).parent / "index.html"
    content = index.read_text()
    assert (
        "main.tsx" in content or "src/main.tsx" in content
    ), "Should reference main.tsx"


def test_index_html_has_viewport():
    """Test that index.html has viewport meta tag."""
    index = Path(__file__).parent / "index.html"
    content = index.read_text()
    assert "viewport" in content, "Should have viewport meta tag"
