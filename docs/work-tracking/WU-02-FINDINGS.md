# WU-02: Root Cause Investigation - Findings

**Status**: In Progress  
**Started**: 2026-01-12  
**Investigation Target**: 500 errors when WebUI calls server

---

## Key Facts

### WU-01 Finding
- All 18 integration tests pass
- Server response formats match client expectations perfectly
- **Conclusion**: 500 errors NOT caused by response format mismatch

### Server Configuration Verified
- ✅ CORS middleware enabled (line 154-160 in main.py)
  - `allow_origins=*` (or configurable via CORS_ORIGINS env var)
  - `allow_credentials=True`
  - `allow_methods=["*"]`
  - `allow_headers=["*"]`

- ✅ Error handling in place
  - Specific HTTPExceptions for 400, 404, 500 errors
  - Generic Exception caught and logged with proper error details
  - logger.exception() used for debugging

- ✅ Dependencies properly injected
  - get_analysis_service(), get_job_service(), get_plugin_service()
  - Services initialized during lifespan startup
  - Fallback error handling if services not initialized

### WebUI Configuration
- API_BASE defaults to `/v1` (relative URL)
- VITE_API_URL env var can override
- No .env file present (using defaults)

---

## Possible Root Causes (To Investigate)

### 1. API Key / Authentication
- Server endpoints may require authentication
- WebUI may not be sending API key in requests
- Check: Is `get_api_key` dependency being satisfied?

### 2. Service Initialization
- Services might not be initialized during startup
- Check: Are plugins loading correctly?
- Check: Is task processor initialized?

### 3. Plugin Loading
- Plugins directory path might be wrong
- Check: FORGESYTE_PLUGINS_DIR env variable
- Check: ../example_plugins relative path valid?

### 4. Database/State Management
- job_store or task_processor might be uninitialized
- Check: Global state in tasks.py

### 5. WebUI Dev Server Proxy
- WebUI dev server (Vite) needs to proxy API requests
- Check: vite.config.ts for proxy configuration
- Default relative `/v1` might not work if server is on different port

---

## Vite Configuration Verified
✅ **vite.config.ts** (lines 17-23):
```javascript
server: {
    port: 3000,
    proxy: {
        "/v1": {
            target: "http://localhost:8000",
            changeOrigin: true,
            ws: true,
        },
    },
},
```

**Verdict**: Proxy correctly configured
- /v1 requests forwarded to localhost:8000
- changeOrigin=true handles cross-origin correctly  
- ws=true enables WebSocket proxying

---

## CRITICAL: Error IS Reproducible

**Error Confirmed**: Yes, 500 error occurs on WebUI startup
**When**: On page load when fetching plugins list
**Error Message**: "API error: 500 Internal Server Error"
**Impact**: Plugin list doesn't load, breaks entire WebUI functionality

---

## Root Cause: Plugin Loading on Startup

The 500 error happens when:
1. WebUI starts
2. Makes GET /v1/plugins request
3. Server returns 500 Internal Server Error

**Investigation Points**:
- Check plugin loading code in main.py (lines 63-84)
- Verify plugins_dir path is correct: `../example_plugins`
- Check if relative path resolves correctly when running server
- Check plugin manager error handling
- Look for any exceptions during plugin discovery

**Likely Issues**:
1. Relative path `../example_plugins` might be wrong depending on where server is started
2. Plugin loading might fail silently and cause 500 in handler
3. PluginManager exception not caught properly
4. Plugins directory doesn't exist or isn't readable

---

## Updated Investigation Plan

**IMMEDIATE ACTIONS**:
1. Check server logs for actual plugin loading error
2. Verify plugins_dir path from working directory
3. Check PluginManager.load_plugins() exception handling
4. Fix plugin loading to properly initialize
5. Test WebUI plugin load after fix
