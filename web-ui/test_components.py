"""Tests for React components."""

from pathlib import Path


def test_app_tsx_exists():
    """Test that App.tsx exists."""
    app = Path(__file__).parent / "src" / "App.tsx"
    assert app.exists(), "src/App.tsx does not exist"


def test_components_directory_exists():
    """Test that components directory exists."""
    components = Path(__file__).parent / "src" / "components"
    assert components.exists(), "src/components directory does not exist"
    assert components.is_dir(), "components should be a directory"


def test_camera_preview_exists():
    """Test that CameraPreview component exists."""
    component = Path(__file__).parent / "src" / "components" / "CameraPreview.tsx"
    assert component.exists(), "src/components/CameraPreview.tsx does not exist"


def test_job_list_exists():
    """Test that JobList component exists."""
    component = Path(__file__).parent / "src" / "components" / "JobList.tsx"
    assert component.exists(), "src/components/JobList.tsx does not exist"


def test_plugin_selector_exists():
    """Test that PluginSelector component exists."""
    component = Path(__file__).parent / "src" / "components" / "PluginSelector.tsx"
    assert component.exists(), "src/components/PluginSelector.tsx does not exist"


def test_results_panel_exists():
    """Test that ResultsPanel component exists."""
    component = Path(__file__).parent / "src" / "components" / "ResultsPanel.tsx"
    assert component.exists(), "src/components/ResultsPanel.tsx does not exist"


def test_app_tsx_has_react():
    """Test that App.tsx imports React."""
    app = Path(__file__).parent / "src" / "App.tsx"
    content = app.read_text()
    assert "import" in content, "App.tsx should have imports"
    assert "React" in content or "react" in content, "App.tsx should import React"


def test_app_tsx_is_component():
    """Test that App.tsx exports a component."""
    app = Path(__file__).parent / "src" / "App.tsx"
    content = app.read_text()
    assert "export" in content, "App.tsx should export something"
    assert (
        "function App" in content or "const App" in content
    ), "App.tsx should define App"
