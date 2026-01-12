#!/usr/bin/env bash
#
# Sync Fixtures - Automated fixture synchronization script
#
# Usage: ./scripts/sync-fixtures.sh
#
# This script:
# 1. Starts the ForgeSyte test server
# 2. Calls real API endpoints
# 3. Captures responses to fixtures/api-responses.json
# 4. Validates responses match expected schema
# 5. Stops the server
#
# Requirements:
# - Python 3.10+ with uv installed
# - Server dependencies installed (uv sync in server/)
# - Server must be startable with: uv run fastapi dev app/main.py
#

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SERVER_DIR="$PROJECT_ROOT/server"
FIXTURES_FILE="$PROJECT_ROOT/fixtures/api-responses.json"
SERVER_PORT=8000
SERVER_HOST="http://localhost:$SERVER_PORT"
MAX_RETRIES=30
RETRY_INTERVAL=1

# Temporary files
TEMP_FIXTURES=$(mktemp)
SERVER_PID=""

# Cleanup on exit
cleanup() {
    if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
        echo -e "${YELLOW}Stopping server (PID: $SERVER_PID)...${NC}"
        kill "$SERVER_PID" 2>/dev/null || true
        sleep 2
        kill -9 "$SERVER_PID" 2>/dev/null || true
    fi
    rm -f "$TEMP_FIXTURES"
}
trap cleanup EXIT

# Error handler
error() {
    echo -e "${RED}❌ Error: $1${NC}" >&2
    exit 1
}

# Success message
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Info message
info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Wait for server to be ready
wait_for_server() {
    local url="$1"
    local retries=0

    info "Waiting for server to be ready at $url..."
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -sf "$url/v1/health" >/dev/null 2>&1; then
            success "Server is ready"
            return 0
        fi
        retries=$((retries + 1))
        sleep $RETRY_INTERVAL
    done

    error "Server did not start within $(($MAX_RETRIES * $RETRY_INTERVAL)) seconds"
}

# Fetch API endpoint and return JSON
fetch_endpoint() {
    local endpoint="$1"
    local url="$SERVER_HOST/v1$endpoint"

    info "Fetching $endpoint..."
    local response=$(curl -sf "$url" 2>/dev/null) || {
        error "Failed to fetch $endpoint"
    }
    echo "$response"
}

# Validate JSON structure
validate_json() {
    local json="$1"
    local description="$2"

    if ! echo "$json" | python3 -m json.tool >/dev/null 2>&1; then
        error "Invalid JSON returned from $description"
    fi
}

# Main script
main() {
    echo ""
    echo "=========================================="
    echo "ForgeSyte Fixture Synchronization"
    echo "=========================================="
    echo ""

    # Check if server directory exists
    if [ ! -d "$SERVER_DIR" ]; then
        error "Server directory not found: $SERVER_DIR"
    fi

    # Check if fixtures directory exists
    if [ ! -d "$PROJECT_ROOT/fixtures" ]; then
        error "Fixtures directory not found: $PROJECT_ROOT/fixtures"
    fi

    # Start server
    info "Starting ForgeSyte server..."
    cd "$SERVER_DIR"
    
    # Start server in background with output to log file
    uv run fastapi dev app/main.py >"$PROJECT_ROOT/server.log" 2>&1 &
    SERVER_PID=$!
    
    info "Server PID: $SERVER_PID"

    # Wait for server to be ready
    wait_for_server "$SERVER_HOST"

    # Initialize fixture object
    local fixtures_json='{'

    # Fetch jobs list endpoint
    info "Fetching /v1/jobs..."
    local jobs_list=$(fetch_endpoint "/jobs?limit=10")
    validate_json "$jobs_list" "GET /v1/jobs"
    fixtures_json+='"jobs_list": '"$jobs_list"','

    # Fetch plugins list endpoint
    info "Fetching /v1/plugins..."
    local plugins_list=$(fetch_endpoint "/plugins")
    validate_json "$plugins_list" "GET /v1/plugins"
    
    # Extract just the plugin array (if response is wrapped)
    if echo "$plugins_list" | grep -q '"plugins"'; then
        plugins_list=$(echo "$plugins_list" | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin)['plugins']))")
    fi
    fixtures_json+='"plugins_list": '"$plugins_list"','

    # Fetch health endpoint
    info "Fetching /v1/health..."
    local health=$(fetch_endpoint "/health")
    validate_json "$health" "GET /v1/health"
    fixtures_json+='"health": '"$health"

    # Try to fetch single job if jobs exist
    info "Fetching single job details..."
    if echo "$jobs_list" | python3 -c "import sys, json; d = json.load(sys.stdin); sys.exit(0 if d.get('jobs') and len(d['jobs']) > 0 else 1)"; then
        local first_job_id=$(echo "$jobs_list" | python3 -c "import sys, json; d = json.load(sys.stdin); print(d['jobs'][0]['job_id'])")
        local job_single=$(fetch_endpoint "/jobs/$first_job_id")
        validate_json "$job_single" "GET /v1/jobs/{id}"
        fixtures_json+=','
        fixtures_json+='"job_single": '"$job_single"
    else
        info "No jobs found in jobs list, skipping single job fetch"
    fi

    # WebSocket frame result is typically not fetchable via HTTP
    # Use a default example from the schema
    info "Adding default frame result example..."
    fixtures_json+=','
    fixtures_json+='"frame_result": {'
    fixtures_json+='"frame_id": "frame-001",'
    fixtures_json+='"plugin": "motion_detector",'
    fixtures_json+='"result": {"motion_detected": true, "confidence": 0.87, "regions": [{"x": 250, "y": 100, "width": 150, "height": 200}]},'
    fixtures_json+='"processing_time_ms": 45'
    fixtures_json+='}'

    # Close JSON
    fixtures_json+='}'

    # Validate complete JSON
    info "Validating complete fixture JSON..."
    if ! echo "$fixtures_json" | python3 -m json.tool >/dev/null 2>&1; then
        error "Generated invalid fixture JSON"
    fi

    # Pretty-print and save
    echo "$fixtures_json" | python3 -m json.tool >"$TEMP_FIXTURES"

    # Backup existing fixtures
    if [ -f "$FIXTURES_FILE" ]; then
        local backup_file="$FIXTURES_FILE.backup.$(date +%s)"
        cp "$FIXTURES_FILE" "$backup_file"
        info "Backed up existing fixtures to: $backup_file"
    fi

    # Write new fixtures
    cp "$TEMP_FIXTURES" "$FIXTURES_FILE"
    success "Fixtures synchronized to: $FIXTURES_FILE"

    # Display summary
    echo ""
    echo "=========================================="
    echo "Sync Summary"
    echo "=========================================="
    local fixture_count=$(echo "$fixtures_json" | python3 -c "import sys, json; d = json.load(sys.stdin); print(len(d))")
    echo "Fixtures captured: $fixture_count"
    echo "Output file: $FIXTURES_FILE"
    echo ""
    echo "Fixtures updated:"
    echo "  - jobs_list"
    echo "  - plugins_list"
    echo "  - health"
    if echo "$jobs_list" | python3 -c "import sys, json; d = json.load(sys.stdin); sys.exit(0 if d.get('jobs') and len(d['jobs']) > 0 else 1)" 2>/dev/null; then
        echo "  - job_single"
    fi
    echo "  - frame_result (default example)"
    echo ""
    success "Fixture synchronization complete!"
}

# Run main function
main "$@"
