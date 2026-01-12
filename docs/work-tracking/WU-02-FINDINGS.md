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

## Conclusion So Far

### What We Know
1. ✅ Response formats are correct (WU-01 verified)
2. ✅ CORS is configured
3. ✅ Error handling is in place
4. ✅ Vite dev server proxy is configured
5. ✅ Services are initialized on startup

### What's Unclear
- Is there an actual 500 error, or was it hypothetical?
- If yes, what's the exact error message?
- Are there specific conditions that trigger it?

---

## Next: Verify With Real Test

To determine if there's an actual issue:
1. Start real server: `cd server && uv run uvicorn app.main:app --reload`
2. Start WebUI dev: `cd web-ui && npm run dev`
3. Open browser, try to load plugins
4. Check browser console and server logs
5. Document actual error (if any)

OR: If no actual 500 errors occur, close the issue as "NOT REPRODUCIBLE"
