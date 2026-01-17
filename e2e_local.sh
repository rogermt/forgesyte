#!/bin/bash

# ForgeSyte E2E Local Test Script
# Runs E2E tests, then tests MCP plugin integration with Gemini-CLI

set -e

echo "🚀 Starting ForgeSyte E2E Local Test Suite..."

# 1. Run standard E2E tests
echo "📋 Step 1: Running E2E tests..."
./e2e.test.sh
E2E_EXIT_CODE=$?

if [ $E2E_EXIT_CODE -ne 0 ]; then
    echo "❌ E2E tests failed (Exit Code: $E2E_EXIT_CODE)"
    exit $E2E_EXIT_CODE
fi

echo "✅ E2E tests passed"

# 2. Test MCP plugin with Gemini-CLI
echo ""
echo "📋 Step 2: Testing MCP plugin with Gemini-CLI..."
echo "Running: gemini -p \"follow instructions in file: @./scripts/gemini-cli-mcp-plugin-test.md\" --m gemini-3-flash-preview --yol"

gemini -p "follow instructions in file: @./scripts/gemini-cli-mcp-plugin-test.md" --m gemini-3-flash-preview --yol
GEMINI_CLI_EXIT_CODE=$?

if [ $GEMINI_CLI_EXIT_CODE -ne 0 ]; then
    echo "❌ Gemini-CLI MCP test failed (Exit Code: $GEMINI_CLI_EXIT_CODE)"
    exit $GEMINI_CLI_EXIT_CODE
fi

echo "✅ Gemini-CLI MCP test passed"

echo ""
echo "✨ All E2E Local Tests PASSED"
exit 0
