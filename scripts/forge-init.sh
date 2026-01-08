#!/usr/bin/env bash
set -euo pipefail

MIN_UV_VERSION="0.4.0"

check_uv_installed() {
    if ! command -v uv >/dev/null 2>&1; then
        echo "uv not found. Installing..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
    fi
}

check_uv_version() {
    INSTALLED=$(uv --version | awk '{print $2}')
    if [ "$(printf '%s\n' "$MIN_UV_VERSION" "$INSTALLED" | sort -V | head -n1)" != "$MIN_UV_VERSION" ]; then
        echo "uv version too old ($INSTALLED). Updating..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
}

create_venv() {
    if [ ! -d ".venv" ]; then
        echo "Creating .venv..."
        uv venv
    else
        echo ".venv already exists."
    fi
}

activate_venv() {
    echo "Activating .venv..."
    # shellcheck disable=SC1091
    source .venv/bin/activate
}

check_uv_installed
check_uv_version
create_venv
activate_venv

echo "ForgeSyte environment ready."
