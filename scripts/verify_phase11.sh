#!/usr/bin/env bash
set -e

echo "=== Phase 11 Verification Script ==="

echo "1. Running server tests..."
cd server
uv run pytest -q

echo "2. Running lint..."
uv run ruff check app/

echo "3. Running type checks..."
uv run mypy app/ --no-site-packages

echo "4. Running plugin health audit..."
python ../scripts/audit_plugins.py

echo "5. Running Phase 9/10 regression tests..."
uv run pytest tests/phase9/ -q
uv run pytest tests/phase10/ -q

echo "6. Running web-ui type checks..."
cd ../web-ui
npm run type-check
npm run lint

echo "=== Phase 11 Verification Complete ==="
