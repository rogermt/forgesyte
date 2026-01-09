#!/usr/bin/env python3
"""
Script to extract Python code from markdown files and recreate the vision-mcp structure
"""

import re
from pathlib import Path


def extract_file_paths_and_content(markdown_content):
    """Extract file paths and their content from markdown with file headers"""
    # Pattern to match file headers like "### `server/app/main.py`" followed by code blocks
    pattern = r"###\s*`(.*?)`\s*\n```(?:python)?\n(.*?)```"
    matches = re.findall(pattern, markdown_content, re.DOTALL)

    # Also look for top-level file definitions like "### `server/app/__init__.py`"
    alt_pattern = r"(\n|^)###\s*`(.*?)`\s*\n```(?:python)?\n(.*?)```"
    alt_matches = re.findall(alt_pattern, markdown_content, re.DOTALL)

    # Process alt_matches to extract just the path and content
    alt_results = [(match[1], match[2]) for match in alt_matches]

    return matches + alt_results


def main():
    # Read the markdown files
    with open("/home/rogermt/forgesyte/scratch/code1.md", "r") as f:
        content1 = f.read()

    with open("/home/rogermt/forgesyte/scratch/code2.md", "r") as f:
        content2 = f.read()

    # Combine content
    all_content = content1 + content2

    # Extract file paths and content
    files = extract_file_paths_and_content(all_content)

    # Create the directory structure and write files
    base_dir = Path("/home/rogermt/forgesyte/original_vision_mcp")

    for filepath, content in files:
        # Clean the filepath (remove any extra spaces or newlines)
        filepath = filepath.strip()

        # Create the full path
        full_path = base_dir / filepath

        # Create parent directories if they don't exist
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the content to the file
        with open(full_path, "w") as f:
            f.write(content.strip())

        print(f"Restored: {full_path}")


if __name__ == "__main__":
    main()
