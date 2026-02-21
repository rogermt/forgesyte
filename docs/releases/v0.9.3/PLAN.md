<think>The user wants me to read the file `/home/rogermt/forgesyte/docs/releases/v0.9.3/POST_MIGRATION FIXES.md` (note there's a space in the filename, so I need to handle that correctly), understand what's required, and provide a plan.

I'm in PLAN MODE, so I should:
1. Read the file to understand what's required
2. Analyze the requirements
3. Provide a detailed plan of what needs to be done
4. Wait for user approval before executing

Let me read the file first.</think>
I'll read the file to understand what's required.
<tool id=call_f400be57a9eb44ada8c133e3>
        <tool_name>read_file</tool_name><tool_result>{"success":true,"tool_name":"read_file","params":{"relative_workspace_path":"/home/rogermt/forgesyte/docs/releases/v0.9.3/POST_MIGRATION FIXES.md","should_read_entire_file":true}}</tool_result>
        <relative_workspace_path>/home/rogermt/forgesyte/docs/releases/v0.9.3/POST_MIGRATION FIXES.md</relative_workspace_path>
        <should_read_entire_file>true</should_read_entire_file>
      </tool>
<think>Now I understand what's required. This is a post-migration cleanup for v0.9.3 after the v0.9.2 unified job system migration. The document outlines:

1. **The Problem**: The old `/v1/analyze` endpoint is still being called by the frontend, but it was removed in v0.9.2 along with `AnalysisService`, `TaskProcessor`, and `JobManagementService`.

2. **The Solution**: A comprehensive cleanup that involves:
   - Frontend changes: Replace `/v1/analyze` and `/v1/analyze-multi` with `/v1/image/submit` and `/v1/jobs/{id}`
   - Backend changes: Remove legacy endpoints, services, and related code
   - Type updates: Update TypeScript types for the new job system

3. **Specific Deliverables**:
   - A bash script for repo-wide search-and-replace
   - TypeScript type updates for `JobResult`
   - API client updates
   - Component updates
   - A backend cleanup script to delete legacy files

Let me create a comprehensive plan for this work. I should:

1. First explore the codebase to understand the current state
2. Identify all files that need changes
3. Plan the specific changes needed
4. Present the plan to the user for approval

Since I'm in PLAN MODE, I should read the relevant files to understand the current state before creating the plan.</think>
I've read the file. This is a **v0.9.3 post-migration cleanup** after the v0.9.2 unified job system migration. The issue is that the frontend is still calling the old `/v1/analyze` endpoint which was removed in v0.9.2.

Let me explore the codebase to understand the current state and create a comprehensive plan.
<tool id=call_69c718616da7423aa52157ce>
        <tool_name>glob</tool_name><tool_result>{"success":true,"tool_name":"glob","params":{"pattern":"**/apiClient.ts","path":"/home/rogermt/forgesyte/web-ui"},"result":"No files found"}</tool_result>
        <pattern>**/apiClient.ts</pattern>
        <path>/home/rogermt/forgesyte/web-ui</path>
      </tool>

<tool id=call_e9b173d37d31405fb44df769>
        <tool_name>glob</tool_name><tool_result>{"success":true,"tool_name":"glob","params":{"pattern":"**/ImageUpload.tsx","path":"/home/rogermt/forgesyte/web-ui"},"result":"No files found"}</tool_result>
        <pattern>**/ImageUpload.tsx</pattern>
        <path>/home/rogermt/forgesyte/web-ui</path>
      </tool>

<tool id=call_85dc96bc181e46d4885bd919>
        <tool_name>glob</tool_name><tool_result>{"success":true,"tool_name":"glob","params":{"pattern":"**/JobStatus.tsx","path":"/home/rogermt/forgesyte/web-ui"},"result":"Found 1 matching file(s)"}</tool_result>
        <pattern>**/JobStatus.tsx</pattern>
        <path>/home/rogermt/forgesyte/web-ui</path>
      </tool>

<tool id=call_f9f0f684046f4c97a4add22a>
        <tool_name>glob</tool_name><tool_result>{"success":true,"tool_name":"glob","params":{"pattern":"**/ToolSelector.tsx","path":"/home/rogermt/forgesyte/web-ui"},"result":"Found 1 matching file(s)"}</tool_result>
        <pattern>**/ToolSelector.tsx</pattern>
        <path>/home/rogermt/forgesyte/web-ui</path>
      </tool>

<tool id=call_ecce69b691884b55858af5d7>
        <tool_name>search_file_content</tool_name><tool_result>{"success":true,"tool_name":"search_file_content","params":{"pattern":"/v1/analyze","path":"/home/rogermt/forgesyte/web-ui/src"},"result":"Found 6 matches"}</tool_result>
        <pattern>/v1/analyze</pattern>
        <path>/home/rogermt/forgesyte/web-ui/src</path>
      </tool>
<think>Good, I found some references to `/v1/analyze` in the frontend. Let me explore more to understand the current structure better.
<tool id=call_f5efdc9a34be4059a16774bd>
        <tool_name>list_directory</tool_name><tool_result>{"success":true,"tool_name":"list_directory","params":{"target_directory":"/home/rogermt/forgesyte/web-ui/src"},"result":"Listed 18 item(s)."}</tool_result>
        <target_directory>/home/rogermt/forgesyte/web-ui/src</target_directory>
      </tool>

<tool id=call_b944a6d11f8644228194c0e2>
        <tool_name>glob</tool_name><tool_result>{"success":true,"tool_name":"glob","params":{"pattern":"**/*.ts","path":"/home/rogermt/forgesyte/web-ui/src"},"result":"Found 30 matching file(s)"}</tool_result>
        <pattern>**/*.ts</pattern>
        <path>/home/rogermt/forgesyte/web-ui/src</path>
      </tool>

<tool id=call_171025f42b8d40e490142c79>
        <tool_name>search_file_content</tool_name><tool_result>{"success":true,"tool_name":"search_file_content","params":{"pattern":"analyzeImage|analyzeMulti","path":"/home/rogermt/forgesyte/web-ui/src"},"result":"Found 35 matches"}</tool_result>
        <pattern>analyzeImage|analyzeMulti</pattern>
        <path>/home/rogermt/forgesyte/web-ui/src</path>
      </tool>
Now I have a good understanding of the current state. Let me read some key files to understand the structure better before creating the plan.
<tool id=call_fa0b3ed2dcc8452c9a620144>
        <tool_name>read_file</tool_name><tool_result>{"success":true,"tool_name":"read_file","params":{"relative_workspace_path":"/home/rogermt/forgesyte/web-ui/src/api/client.ts","should_read_entire_file":true}}</tool_result>
        <relative_workspace_path>/home/rogermt/forgesyte/web-ui/src/api/client.ts</relative_workspace_path>
        <should_read_entire_file>true</should_read_entire_file>
      </tool>

<tool id=call_39db8af09a004b34a38a4fb5>
        <tool_name>read_file</tool_name><tool_result>{"success":true,"tool_name":"read_file","params":{"relative_workspace_path":"/home/rogermt/forgesyte/web-ui/src/App.tsx","should_read_entire_file":true}}</tool_result>
        <relative_workspace_path>/home/rogermt/forgesyte/web-ui/src/App.tsx</relative_workspace_path>
        <should_read_entire_file>true</should_read_entire_file>
      </tool>

<tool id=call_15115de4612b47a4abd3d26f>
        <tool_name>search_file_content</tool_name><tool_result>{"success":true,"tool_name":"search_file_content","params":{"pattern":"/v1/analyze|AnalysisService|TaskProcessor|JobManagementService","path":"/home/rogermt/forgesyte/server/app"},"result":"Found 92 matches"}</tool_result>
        <pattern>/v1/analyze|AnalysisService|TaskProcessor|JobManagementService</pattern>
        <path>/home/rogermt/forgesyte/server/app</path>
      </tool>
Now I have a good understanding of the current state. Let me read a few more key files to understand the structure better before creating the plan.
<tool id=call_1594176575b740ac9762923d>
        <tool_name>read_file</tool_name><tool_result>{"success":true,"tool_name":"read_file","params":{"relative_workspace_path":"/home/rogermt/forgesyte/web-ui/src/components/ImageMultiToolForm.tsx","should_read_entire_file":true}}</tool_result>
        <relative_workspace_path>/home/rogermt/forgesyte/web-ui/src/components/ImageMultiToolForm.tsx</relative_workspace_path>
        <should_read_entire_file>true</should_read_entire_file>
      </tool>

<tool id=call_a858901058b84fc9a7a10fac>
        <tool_name>read_file</tool_name><tool_result>{"success":true,"tool_name":"read_file","params":{"relative_workspace_path":"/home/rogermt/forgesyte/server/app/api.py","should_read_entire_file":true}}</tool_result>
        <relative_workspace_path>/home/rogermt/forgesyte/server/app/api.py</relative_workspace_path>
        <should_read_entire_file>true</should_read_entire_file>
      </tool>

<tool id=call_508409dd06fb4c5492f471a2>
        <tool_name>search_file_content</tool_name><tool_result>{"success":true,"tool_name":"search_file_content","params":{"pattern":"@router\\.post.*analyze","path":"/home/rogermt/forgesyte/server/app/api_routes"},"result":"No matches found"}</tool_result>
        <pattern>@router\.post.*analyze</pattern>
        <path>/home/rogermt/forgesyte/server/app/api_routes</path>
      </tool>
Let me search more for the legacy analyze endpoint.
<tool id=call_19536fc246204e0da2759b3e>
        <tool_name>search_file_content</tool_name><tool_result>{"success":true,"tool_name":"search_file_content","params":{"pattern":"@router\\.post.*analyze","path":"/home/rogermt/forgesyte/server/app/api.py"},"result":"Found 3 matches"}</tool_result>
        <pattern>@router\.post.*analyze</pattern>
        <path>/home/rogermt/forgesyte/server/app/api.py</path>
      </tool>

<tool id=call_e5e9593041b1436db9017226>
        <tool_name>list_directory</tool_name><tool_result>{"success":true,"tool_name":"list_directory","params":{"target_directory":"/home/rogermt/forgesyte/server/app/api_routes/routes"},"result":"Listed 9 item(s)."}</tool_result>
        <target_directory>/home/rogermt/forgesyte/server/app/api_routes/routes</target_directory>
      </tool>

<tool id=call_f92fc746cfcd48cda6fe2d4d>
        <tool_name>glob</tool_name><tool_result>{"success":true,"tool_name":"glob","params":{"pattern":"**/analyze*.py","path":"/home/rogermt/forgesyte/server/app"},"result":"No files found"}</tool_result>
        <pattern>**/analyze*.py</pattern>
        <path>/home/rogermt/forgesyte/server/app</path>
      </tool>
Now let me look at the analyze endpoints in api.py to understand what needs to be removed.
<tool id=call_2fbdaaf4ed9043589566e799>
        <tool_name>read_file</tool_name><tool_result>{"success":true,"tool_name":"read_file","params":{"relative_workspace_path":"/home/rogermt/forgesyte/server/app/api.py","should_read_entire_file":true}}</tool_result>
        <relative_workspace_path>/home/rogermt/forgesyte/server/app/api.py</relative_workspace_path>
        <should_read_entire_file>true</should_read_entire_file>
      </tool>

<tool id=call_28706e1f09de4b3199614a69>
        <tool_name>read_file</tool_name><tool_result>{"success":true,"tool_name":"read_file","params":{"relative_workspace_path":"/home/rogermt/forgesyte/server/app/api.py","should_read_entire_file":true}}</tool_result>
        <relative_workspace_path>/home/rogermt/forgesyte/server/app/api.py</relative_workspace_path>
        <should_read_entire_file>true</should_read_entire_file>
      </tool>

<tool id=call_b68d9477731a48e180fab673>
        <tool_name>list_directory</tool_name><tool_result>{"success":true,"tool_name":"list_directory","params":{"target_directory":"/home/rogermt/forgesyte/server/app/services"},"result":"Listed 21 item(s)."}</tool_result>
        <target_directory>/home/rogermt/forgesyte/server/app/services</target_directory>
      </tool>
Now I have a good understanding of the current state. Let me create a comprehensive plan for the v0.9.3 post-migration cleanup. Based on my analysis:

## Current State:

### Frontend (web-ui):
1. **apiClient.ts** has:
   - `analyzeImage()` - calls `/v1/analyze` (LEGACY)
   - `analyzeMulti()` - calls `/v1/image/analyze-multi` (LEGACY)
   - `submitImage()` - calls `/v1/image/submit` (NEW - correct)
   - `submitVideo()` - calls `/v1/video/submit` (NEW - correct)
   - `getJob()` - calls `/v1/jobs/{id}` (NEW - correct)
   - `getVideoJobStatus()` - calls `/v1/video/status/{id}` (LEGACY?)
   - `getVideoJobResults()` - calls `/v1/video/results/{id}` (LEGACY?)

2. **App.tsx**:
   - Uses `apiClient.analyzeImage()` in `handleFileUpload` (LEGACY)
   - Has `ImageMultiToolForm` component that uses `analyzeMulti()` (LEGACY)

3. **ImageMultiToolForm.tsx**:
   - Uses `apiClient.analyzeMulti()` (LEGACY)

4. **Integration tests**:
   - `server-api.integration.test.ts` - tests `/v1/analyze` endpoint
   - `multi-tool-ui.integration.test.tsx` - tests `analyzeMulti()`

5. **Component tests**:
   - `ImageMultiToolForm.test.tsx` - tests `analyzeMulti()`

### Backend (server):
1. **api.py** has:
   - `@router.post("/analyze")` - LEGACY endpoint (depends on AnalysisService)
   - `@router.post("/analyze/json")` - LEGACY endpoint
   - `@router.post("/image/analyze-multi")` - LEGACY endpoint
   - `get_analysis_service()` - dependency injection for AnalysisService
   - `get_job_service()` - dependency injection for JobManagementService

2. **Services**:
   - `analysis_service.py` - LEGACY service
   - `job_management_service.py` - LEGACY service

3. **main.py**:
   - Lines 66, 219, 225-226 indicate TaskProcessor was removed in v0.9.2
   - But `app.state.analysis_service_rest` may still be used by legacy endpoints

I'll focus on removing legacy components and updating the frontend to use the new unified job system. The key actions involve deleting outdated endpoints, services, and components, while ensuring proper migration to the new API structure.</think>
Now I have a comprehensive understanding of the current state. Let me create a detailed plan for the v0.9.3 post-migration cleanup.

---

## 📋 v0.9.3 Post-Migration Cleanup Plan

### 🎯 Objective
Remove all legacy endpoints and services from v0.9.2 migration, ensuring frontend uses the new unified job system (`/v1/image/submit` + `/v1/jobs/{id}`).

---

### 📊 Current State Analysis

#### **Frontend Issues:**
- `apiClient.analyzeImage()` still calls `/v1/analyze` (legacy endpoint)
- `apiClient.analyzeMulti()` still calls `/v1/image/analyze-multi` (legacy endpoint)
- `App.tsx` uses `analyzeImage()` in `handleFileUpload`
- `ImageMultiToolForm.tsx` uses `analyzeMulti()`
- Integration tests test legacy endpoints
- Component tests test legacy `analyzeMulti()`

#### **Backend Issues:**
- `api.py` has 3 legacy endpoints:
  - `POST /analyze`
  - `POST /analyze/json`
  - `POST /image/analyze-multi`
- `get_analysis_service()` and `get_job_service()` dependency injectors for legacy services
- Legacy services still exist:
  - `services/analysis_service.py`
  - `services/job_management_service.py`

---

### ✅ Implementation Plan

#### **Phase 1: Frontend Cleanup (web-ui/)**

**1.1 Update `src/api/client.ts`:**
- Remove `analyzeImage()` method (lines ~111-160)
- Remove `analyzeMulti()` method (lines ~240-290)
- Remove `getVideoJobStatus()` method (if duplicate of `getJob()`)
- Remove `getVideoJobResults()` method (if duplicate of `getJob()`)
- Update `AnalysisResult` type (no longer needed)
- Keep `submitImage()`, `submitVideo()`, `getJob()` (these are correct)

**1.2 Update `src/App.tsx`:**
- Replace `apiClient.analyzeImage()` call with `apiClient.submitImage()` in `handleFileUpload`
- Remove `ImageMultiToolForm` import and usage
- Remove "multi-tool-image" from `ViewMode` type
- Remove multi-tool button from navigation

**1.3 Delete `src/components/ImageMultiToolForm.tsx`:**
- Remove entire file

**1.4 Delete `src/components/ImageMultiToolForm.test.tsx`:**
- Remove entire file

**1.5 Update `src/integration/server-api.integration.test.ts`:**
- Remove tests for `POST /v1/analyze` (lines ~233-380)
- Update to test `/v1/image/submit` instead

**1.6 Update `src/integration/multi-tool-ui.integration.test.tsx`:**
- Remove entire file (multi-tool UI is being removed)

**1.7 Update `src/App.tdd.test.tsx`:**
- Remove `analyzeImage` mock
- Update to mock `submitImage` instead

**1.8 Update `src/api/client.test.ts`:**
- Remove `analyzeImage` tests (lines ~163-215)
- Remove `analyzeMulti` tests (lines ~517-620)
- Add tests for `submitImage` if not present

---

#### **Phase 2: Backend Cleanup (server/)**

**2.1 Update `app/api.py`:**
- Remove `POST /analyze` endpoint (lines ~122-275)
- Remove `POST /analyze/json` endpoint (lines ~276-366)
- Remove `POST /image/analyze-multi` endpoint (lines ~367-430)
- Remove `get_analysis_service()` dependency injector (lines ~66-79)
- Remove `get_job_service()` dependency injector (lines ~83-96)
- Remove imports of `AnalysisService` and `JobManagementService`
- Update docstring to reflect removed endpoints

**2.2 Delete legacy service files:**
- Delete `app/services/analysis_service.py`
- Delete `app/services/job_management_service.py`

**2.3 Update `app/main.py`:**
- Remove any initialization of `analysis_service_rest` (line ~226)
- Remove any references to legacy services in comments

**2.4 Update tests:**
- Search for and update any tests that reference legacy endpoints or services
- Remove tests for `POST /analyze`, `POST /analyze/json`, `POST /image/analyze-multi`

---

#### **Phase 3: Type Updates**

**3.1 Update `src/types/plugin.ts` or create `src/types/JobResult.ts`:**
- Ensure `Job` type matches unified job system response:
  ```typescript
  interface Job {
    job_id: string;
    status: "queued" | "running" | "done" | "error" | "not_found";
    plugin: string;
    result?: Record<string, unknown>;  // Changed from 'results'
    error?: string | null;
    created_at: string;
    completed_at?: string | null;
    progress?: number | null;
  }
  ```

---

#### **Phase 4: Verification**

**4.1 Run frontend tests:**
```bash
cd web-ui
npm run lint
npm run type-check
npm run test -- --run
```

**4.2 Run backend tests:**
```bash
cd server
uv run pytest tests/ -v
```

**4.3 Run execution governance verification:**
```bash
python scripts/scan_execution_violations.py
cd server && uv run pytest tests/plugins -v
cd server && uv run pytest tests/execution -v
```

---

### 📝 Files to Modify

#### **Frontend (web-ui/):**
1. `src/api/client.ts` - Remove legacy methods
2. `src/App.tsx` - Update to use new API
3. `src/types/plugin.ts` - Update Job type if needed

#### **Frontend Files to Delete:**
1. `src/components/ImageMultiToolForm.tsx`
2. `src/components/ImageMultiToolForm.test.tsx`
3. `src/integration/multi-tool-ui.integration.test.tsx`

#### **Backend (server/):**
1. `app/api.py` - Remove legacy endpoints and dependency injectors
2. `app/main.py` - Remove legacy service initialization

#### **Backend Files to Delete:**
1. `app/services/analysis_service.py`
2. `app/services/job_management_service.py`

---

### ⚠️ Risk Assessment

**Low Risk:**
- Legacy endpoints are already non-functional (AnalysisService not initialized)
- Frontend has new methods (`submitImage`, `getJob`) that work correctly

**Medium Risk:**
- Integration tests need careful updates
- Need to ensure no other code references the removed endpoints

**Mitigation:**
- Run full test suite after changes
- Use search to find all references before deletion
- Commit changes in phases for easy rollback

---

### 🎯 Success Criteria

1. ✅ No frontend code calls `/v1/analyze` or `/v1/analyze-multi`
2. ✅ No frontend code calls `analyzeImage()` or `analyzeMulti()`
3. ✅ All image/video submissions use `submitImage()` or `submitVideo()`
4. ✅ All job polling uses `getJob()`
5. ✅ Backend has no `/analyze`, `/analyze/json`, or `/image/analyze-multi` endpoints
6. ✅ Legacy services (`AnalysisService`, `JobManagementService`) are deleted
7. ✅ All tests pass (frontend lint, type-check, tests; backend pytest)
8. ✅ Execution governance verification passes

---

**Ready to proceed?** Please approve and I'll execute this plan in the following order:
1. Frontend cleanup (Phase 1)
2. Type updates (Phase 3)
3. Backend cleanup (Phase 2)
4. Verification (Phase 4)