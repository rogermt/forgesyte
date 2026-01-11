# Issue: Implement & Test Gemini-CLI Extension Installation of ForgeSyte

**Status:** 🔴 TODO  
**Priority:** HIGH  
**Type:** Feature  
**Estimated:** 6-8 hours  

---

## Description

Implement and test a seamless installation mechanism for ForgeSyte as a Gemini-CLI MCP extension. Users should be able to install ForgeSyte with a single command and have it automatically configured in their Gemini settings.

---

## Background

Currently:
- ✅ ForgeSyte MCP server is fully functional
- ✅ Gemini-CLI can discover and use ForgeSyte tools (manual setup required)
- ❌ No automated installation/configuration mechanism
- ❌ Users must manually edit `~/.gemini/settings.json`

Users need:
1. Simple installation command
2. Automatic server startup management
3. Configuration in Gemini-CLI settings
4. Verification that extension is working

---

## Acceptance Criteria

### AC1: Installation Command Works
```bash
gemini extension install forgesyte
# or
npm install -g forgesyte
```
✅ Installs ForgeSyte package  
✅ Registers as Gemini extension  
✅ Auto-configures `~/.gemini/settings.json`  

### AC2: Server Auto-Start
- ✅ ForgeSyte server starts automatically when Gemini uses it
- ✅ Server restarts on failure (retry logic)
- ✅ Server stops cleanly on Gemini exit
- ✅ Port selection (auto-find available port if 8000 in use)

### AC3: Configuration Management
- ✅ Auto-add to `~/.gemini/settings.json`:
  ```json
  {
    "mcpServers": {
      "forgesyte": {
        "httpUrl": "http://localhost:PORT/v1/mcp",
        "timeout": 30000,
        "description": "ForgeSyte AI-vision MCP server"
      }
    }
  }
  ```
- ✅ Handle existing configs (merge, don't overwrite)
- ✅ Create backup before modifying

### AC4: Verification & Testing
- ✅ `gemini /mcp` shows "🟢 forgesyte - Ready (4 tools)"
- ✅ Can invoke tools via Gemini CLI
- ✅ WebSocket streaming works
- ✅ Errors are user-friendly

### AC5: Documentation
- ✅ Installation guide in README.md
- ✅ Troubleshooting common issues
- ✅ Uninstall instructions

---

## Technical Tasks

### Phase 1: Package & Distribution (2h)

- [ ] Create installation script `scripts/install.sh` (Linux/Mac)
- [ ] Create installation script `scripts/install.ps1` (Windows)
- [ ] Update `package.json` with `bin` entry for global install
- [ ] Create `setup.py` or `pyproject.toml` for pip installation
- [ ] Test: `npm install -g forgesyte` works
- [ ] Test: `uv pip install forgesyte` works

**Deliverable:**
```bash
npm install -g forgesyte
# or
uv pip install forgesyte
```

### Phase 2: Server Lifecycle Management (2h)

- [ ] Create server process manager (`scripts/server-manager.py` or similar)
  - Start/stop/restart functionality
  - Daemonize on Unix, service on Windows
  - Port auto-detection (if 8000 busy)
  - PID file for process tracking

- [ ] Create Gemini integration hook
  - Detect when Gemini connects
  - Start ForgeSyte server if not running
  - Stop server on cleanup

- [ ] Test:
  - Server auto-starts when Gemini uses it
  - Server restarts on failure
  - Multiple concurrent Gemini clients work
  - Server stops on Gemini exit

**Deliverable:**
```bash
forgesyte-server start    # Start background server
forgesyte-server stop     # Stop server
forgesyte-server status   # Check status
```

### Phase 3: Configuration Management (1.5h)

- [ ] Create config manager (`scripts/config-manager.py`)
  - Auto-detect Gemini settings location
  - Parse existing `~/.gemini/settings.json`
  - Merge ForgeSyte MCP config
  - Create backup before modification
  - Validate final config

- [ ] Create installation wizard
  - Ask user for server hostname/port
  - Auto-add to Gemini settings
  - Verify connection works

- [ ] Test:
  - Config merges without overwriting existing servers
  - Backups created properly
  - Invalid configs don't break Gemini

**Deliverable:**
```bash
forgesyte configure      # Interactive setup
forgesyte verify         # Test connection
```

### Phase 4: Verification & Diagnostics (1h)

- [ ] Create verification script (`scripts/verify.py`)
  - Check server is running
  - Test MCP endpoint responds
  - Verify all 4 tools discoverable
  - Test tool invocation
  - Display any errors

- [ ] Create diagnostic command
  ```bash
  forgesyte diagnose
  # Output: ✅ Server running, ✅ Tools discoverable, ✅ Streaming works
  ```

**Deliverable:**
```bash
forgesyte diagnose       # Full system check
gemini /mcp              # Shows forgesyte ready
```

### Phase 5: Documentation & Testing (1.5h)

- [ ] Update README.md with installation section
- [ ] Create INSTALLATION.md guide
- [ ] Create TROUBLESHOOTING.md
- [ ] Add test suite for installation workflow
- [ ] Test on Mac, Linux, Windows (WSL)

**Deliverable:**
- Installation guide: 500+ words
- Troubleshooting guide: Common issues + fixes
- Test suite: 10+ tests for lifecycle management

---

## Implementation Plan

### Work Units (1-2 hours each)

**WU-01: Distribution & Packaging** (2h)
- npm bin entry
- pip installation
- version pinning
- Acceptance: `npm install -g forgesyte` installs globally

**WU-02: Process Management** (2h)
- Server start/stop/restart
- Port auto-detection
- Daemonization (Unix) / Service (Windows)
- Acceptance: `forgesyte-server start` launches background process

**WU-03: Configuration Setup** (1.5h)
- Gemini settings detection
- Config merging
- Backup creation
- Acceptance: `forgesyte configure` auto-adds to ~/.gemini/settings.json

**WU-04: Verification & Diagnostics** (1h)
- Health check endpoint
- Tool discovery verification
- Streaming test
- Acceptance: `forgesyte diagnose` shows all green

**WU-05: Documentation & Testing** (1.5h)
- Installation guide
- Troubleshooting guide
- Integration tests
- Acceptance: All 4 platforms can install and use

---

## Definition of Done

- [ ] All 4 work units complete
- [ ] Installation tested on Mac, Linux, Windows
- [ ] `gemini /mcp` shows "🟢 forgesyte - Ready (4 tools)"
- [ ] Tools work via Gemini CLI
- [ ] Error messages are user-friendly
- [ ] Documentation complete and tested
- [ ] No breaking changes to existing API
- [ ] All tests passing (307+ total)

---

## Testing Checklist

### Manual Testing

- [ ] **Fresh Install (Mac/Linux):**
  ```bash
  npm install -g forgesyte
  forgesyte configure
  gemini /mcp
  ```
  Expected: ✅ forgesyte shows as Ready with 4 tools

- [ ] **Fresh Install (Windows WSL):**
  Same as above, verify path handling

- [ ] **Existing Gemini Config:**
  - Install ForgeSyte with existing servers configured
  - Verify other servers still work

- [ ] **Server Lifecycle:**
  - Kill ForgeSyte server
  - Ask Gemini to use tool
  - Verify server auto-restarts

- [ ] **Tool Invocation:**
  - Invoke each of 4 tools via Gemini CLI
  - Verify results returned correctly

### Automated Testing

- [ ] Unit tests for config manager
- [ ] Unit tests for process manager
- [ ] Integration test: full install flow
- [ ] Integration test: tool invocation flow
- [ ] E2E test with Gemini CLI (if possible)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Port 8000 already in use | Server won't start | Auto-detect free port, let user choose |
| Invalid Gemini settings | Breaks Gemini | Validate JSON, backup before modify |
| Server crashes on startup | Silent failure | Health check + auto-restart with exponential backoff |
| Different platforms (Mac/Linux/Windows) | Installation fails | Test on all 3, use platform-specific scripts |
| User has old ForgeSyte version | Conflicts | Check version, upgrade path |

---

## Resources

**Related Files:**
- `server/app/main.py` – FastAPI server
- `server/app/mcp_routes.py` – MCP endpoint
- `.gemini/settings.json` – Gemini config location
- `gemini_extension_manifest.json` – Extension metadata

**Dependencies:**
- Click (CLI framework)
- Pydantic (config validation)
- Requests (HTTP verification)

---

## Success Metrics

✅ Installation takes <1 minute  
✅ User can invoke ForgeSyte tools in Gemini CLI immediately  
✅ Error messages are clear and actionable  
✅ 95%+ installation success rate in testing  
✅ Users never need to manually edit config files  

---

**Created:** 2026-01-11  
**Target:** End of current sprint  
**Assigned to:** Next available developer
