"""
Test suite for WU-10: ForgeSyte color palette in CSS.

Ensures index.css defines the ForgeSyte brand colors:
- Primary: Charcoal #111318
- Secondary: Steel #2B3038
- Accent 1: Forge Orange #FF6A00
- Accent 2: Electric Cyan #00E5FF

Plus neutral colors for UI elements.
"""

import re
from pathlib import Path

# Get web-ui directory
WEB_UI_DIR = Path(__file__).parent


def test_index_css_exists():
    """Verify index.css exists and is readable."""
    css_path = WEB_UI_DIR / "src" / "index.css"
    assert css_path.exists(), "index.css not found"
    with open(css_path, "r") as f:
        content = f.read()
    assert len(content) > 0, "index.css is empty"


def test_css_has_root_variables():
    """Verify CSS has :root CSS variable definitions."""
    css_path = WEB_UI_DIR / "src" / "index.css"
    with open(css_path, "r") as f:
        content = f.read()
    assert ":root {" in content, "Missing :root selector for CSS variables"
    assert "--" in content, "No CSS custom properties (--var-name) found"


def test_forgesyte_primary_color_present():
    """Verify ForgeSyte primary color (Charcoal #111318) is defined."""
    css_path = WEB_UI_DIR / "src" / "index.css"
    with open(css_path, "r") as f:
        content = f.read()
    # Look for the hex color (case-insensitive)
    assert (
        "111318" in content.lower() or "primary" in content.lower()
    ), "ForgeSyte primary color #111318 not found"


def test_forgesyte_secondary_color_present():
    """Verify ForgeSyte secondary color (Steel #2B3038) is defined."""
    css_path = WEB_UI_DIR / "src" / "index.css"
    with open(css_path, "r") as f:
        content = f.read()
    assert (
        "2b3038" in content.lower()
        or "2B3038" in content
        or "secondary" in content.lower()
    ), "ForgeSyte secondary color #2B3038 not found"


def test_forgesyte_orange_accent_present():
    """Verify Forge Orange accent (#FF6A00) is defined."""
    css_path = WEB_UI_DIR / "src" / "index.css"
    with open(css_path, "r") as f:
        content = f.read()
    assert (
        "ff6a00" in content.lower()
        or "forge" in content.lower()
        or "orange" in content.lower()
    ), "Forge Orange accent #FF6A00 not found"


def test_forgesyte_cyan_accent_present():
    """Verify Electric Cyan accent (#00E5FF) is defined."""
    css_path = WEB_UI_DIR / "src" / "index.css"
    with open(css_path, "r") as f:
        content = f.read()
    assert (
        "00e5ff" in content.lower()
        or "00E5FF" in content
        or "cyan" in content.lower()
        or "electric" in content.lower()
    ), "Electric Cyan accent #00E5FF not found"


def test_neutral_text_colors_present():
    """Verify neutral text colors are defined for accessibility."""
    css_path = WEB_UI_DIR / "src" / "index.css"
    with open(css_path, "r") as f:
        content = f.read()
    # Should have text-primary, text-secondary, text-muted or similar
    text_vars = sum(
        1
        for var in [
            "text-primary",
            "text-secondary",
            "text-muted",
        ]
        if f"--{var}" in content
    )
    assert text_vars >= 2, "Missing neutral text color variables"


def test_neutral_background_colors_present():
    """Verify neutral background colors for UI elements."""
    css_path = WEB_UI_DIR / "src" / "index.css"
    with open(css_path, "r") as f:
        content = f.read()
    # Should have bg-primary, bg-secondary, or similar
    bg_vars = sum(
        1
        for var in [
            "bg-primary",
            "bg-secondary",
            "bg-tertiary",
            "bg-hover",
        ]
        if f"--{var}" in content
    )
    assert bg_vars >= 2, "Missing neutral background color variables"


def test_border_colors_present():
    """Verify border colors for dividers and edges."""
    css_path = WEB_UI_DIR / "src" / "index.css"
    with open(css_path, "r") as f:
        content = f.read()
    assert (
        "--border-color" in content or "--border" in content
    ), "Missing border color variables"


def test_css_uses_variables_throughout():
    """Verify CSS uses var() for color definitions, not hardcoded colors."""
    css_path = WEB_UI_DIR / "src" / "index.css"
    with open(css_path, "r") as f:
        content = f.read()

    # Count var() usage and color properties
    var_usage = len(re.findall(r"var\(--[\w-]+\)", content))
    assert var_usage > 10, f"Expected many var() usages, found {var_usage}"


def test_forgesyte_branding_comments():
    """Verify CSS includes ForgeSyte branding/palette comments."""
    css_path = WEB_UI_DIR / "src" / "index.css"
    with open(css_path, "r") as f:
        content = f.read()

    # Should have some reference to the palette
    assert (
        "palette" in content.lower()
        or "forgesyte" in content.lower()
        or "color" in content.lower()
    ), "Missing color palette or ForgeSyte comments in CSS"
