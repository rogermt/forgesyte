"""Tests for .gitignore and environment files."""

from pathlib import Path


def test_gitignore_exists():
    """Test that .gitignore exists."""
    gitignore = Path(__file__).parent / ".gitignore"
    assert gitignore.exists(), ".gitignore does not exist"


def test_gitignore_has_node_modules():
    """Test that .gitignore excludes node_modules."""
    gitignore = Path(__file__).parent / ".gitignore"
    content = gitignore.read_text()
    assert "node_modules" in content, ".gitignore should exclude node_modules"


def test_gitignore_has_dist():
    """Test that .gitignore excludes dist."""
    gitignore = Path(__file__).parent / ".gitignore"
    content = gitignore.read_text()
    assert "dist" in content, ".gitignore should exclude dist"


def test_gitignore_has_env():
    """Test that .gitignore excludes .env.local."""
    gitignore = Path(__file__).parent / ".gitignore"
    content = gitignore.read_text()
    assert (
        ".env.local" in content or ".env" in content
    ), ".gitignore should exclude .env files"


def test_env_example_exists():
    """Test that .env.example exists."""
    env_example = Path(__file__).parent / ".env.example"
    assert env_example.exists(), ".env.example does not exist"


def test_env_example_has_variables():
    """Test that .env.example documents required variables."""
    env_example = Path(__file__).parent / ".env.example"
    content = env_example.read_text()
    assert "VITE_" in content, ".env.example should have VITE_ variables"


def test_nvmrc_exists():
    """Test that .nvmrc exists."""
    nvmrc = Path(__file__).parent / ".nvmrc"
    assert nvmrc.exists(), ".nvmrc does not exist"


def test_nvmrc_has_node_version():
    """Test that .nvmrc specifies Node version."""
    nvmrc = Path(__file__).parent / ".nvmrc"
    content = nvmrc.read_text().strip()
    assert content.isdigit() or "." in content, ".nvmrc should contain Node version"
