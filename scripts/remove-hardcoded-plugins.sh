#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="server/app"

# Forbidden plugin references (exact tokens, including trailing spaces)
PLUGINS=(
  "ocr_plugin"
  "motion_detector"
  "OCRPlugin"
  "MotionDetectorPlugin"
  "ocr "                # <-- trailing space preserved
  "yolo "               # <-- trailing space preserved
  "yolo-tracker"
  "forgesyte-yolo-tracker"
)

echo "=== ForgeSyte Hardcoded Plugin Import Removal ==="
echo "Scanning under: $ROOT_DIR"
echo

MODIFIED=0

for plugin in "${PLUGINS[@]}"; do
    echo "Searching for: '$plugin'"

    # Find all files containing the exact token
    matches=$(grep -RIl "$plugin" "$ROOT_DIR" || true)

    if [[ -z "$matches" ]]; then
        echo "  No occurrences found."
        echo
        continue
    fi

    echo "  Found in:"
    echo "$matches" | sed 's/^/    - /'
    echo

    # Remove entire lines containing the token
    while IFS= read -r file; do
        echo "  Cleaning: $file"
        sed -i.bak "/$plugin/d" "$file"
        rm "$file.bak"
        MODIFIED=$((MODIFIED+1))
    done <<< "$matches"

    echo
done

echo "=== Done ==="
echo "Modified files: $MODIFIED"
