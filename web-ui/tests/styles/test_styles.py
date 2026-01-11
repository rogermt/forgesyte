"""Tests for main.tsx and index.css."""

from pathlib import Path


def test_main_tsx_exists():
    """Test that src/main.tsx exists."""
    main = Path(__file__).parent / "src" / "main.tsx"
    assert main.exists(), "src/main.tsx does not exist"


def test_main_tsx_imports_react():
    """Test that main.tsx imports React and ReactDOM."""
    main = Path(__file__).parent / "src" / "main.tsx"
    content = main.read_text()
    assert "React" in content, "Should import React"
    assert "ReactDOM" in content, "Should import ReactDOM"


def test_main_tsx_imports_app():
    """Test that main.tsx imports App component."""
    main = Path(__file__).parent / "src" / "main.tsx"
    content = main.read_text()
    assert "App" in content, "Should import App component"


def test_main_tsx_creates_root():
    """Test that main.tsx creates React root."""
    main = Path(__file__).parent / "src" / "main.tsx"
    content = main.read_text()
    assert (
        "createRoot" in content or "root" in content.lower()
    ), "Should create React root"


def test_index_css_exists():
    """Test that src/index.css exists."""
    css = Path(__file__).parent / "src" / "index.css"
    assert css.exists(), "src/index.css does not exist"


def test_index_css_has_base_styles():
    """Test that index.css has base styles."""
    css = Path(__file__).parent / "src" / "index.css"
    content = css.read_text()
    assert "{" in content and "}" in content, "Should have CSS rules"
    # Check for common resets or base styles
    assert (
        "margin" in content.lower()
        or "padding" in content.lower()
        or "font" in content.lower()
    ), "Should have base element styles"
