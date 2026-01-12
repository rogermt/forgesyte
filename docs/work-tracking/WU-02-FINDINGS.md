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

## Next Steps

1. Check vite.config.ts for API proxy configuration
2. Review WebUI startup logs for errors
3. Start server and WebUI, test real request
4. Check browser console for network errors
5. Check server logs for actual 500 error details

---

## Investigation Checklist

- [ ] Examine vite.config.ts proxy settings
- [ ] Start server on port 8000
- [ ] Start WebUI dev server on port 5173 (typical Vite default)
- [ ] Test `/v1/plugins` call from WebUI
- [ ] Check browser network tab for actual response
- [ ] Check server logs for error details
- [ ] Verify plugins load correctly
- [ ] Document actual error message
