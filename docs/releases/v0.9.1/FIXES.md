<think>The user wants me to look at two files related to v0.9.1 fixes:
1. /home/rogermt/forgesyte/docs/releases/v0.9.1/FIX_RELEATIVE_PATHS.md
2. /home/rogermt/forgesyte/docs/releases/v0.9.1/FIX_RESULTS_FILE.md

They want me to:
1. Read these fix documents
2. Look at the actual codebase to understand the context
3. Create a plan for implementing these fixes
4. Ask questions if I'm less than 95% confident

I'm in PLAN MODE, so I should NOT execute any file modifications. I should:
- Read the fix documents
- Explore the relevant code
- Create a detailed implementation plan
- Ask clarifying questions if needed

Let me start by reading both fix documents.</think>
I'll examine both fix documents and the relevant codebase to create an implementation plan.
<tool id=call_342dcd7e62fa440f8d8c69cf>
        <tool_name>read_file</tool_name><tool_result>%7B%22success%22%3Atrue%2C%22tool_name%22%3A%22read_file%22%2C%22params%22%3A%7B%22relative_workspace_path%22%3A%22%2Fhome%2Frogermt%2Fforgesyte%2Fdocs%2Freleases%2Fv0.9.1%2FFIX_RELEATIVE_PATHS.md%22%2C%22should_read_entire_file%22%3Atrue%7D%7D</tool_result>
        <relative_workspace_path>/home/rogermt/forgesyte/docs/releases/v0.9.1/FIX_RELEATIVE_PATHS.md</relative_workspace_path>
        <should_read_entire_file>true</should_read_entire_file>
      </tool>

<tool id=call_8b0eac7a64ba480fb2121d23>
        <tool_name>read_file</tool_name><tool_result>%7B%22success%22%3Atrue%2C%22tool_name%22%3A%22read_file%22%2C%22params%22%3A%7B%22relative_workspace_path%22%3A%22%2Fhome%2Frogermt%2Fforgesyte%2Fdocs%2Freleases%2Fv0.9.1%2FFIX_RESULTS_FILE.md%22%2C%22should_read_entire_file%22%3Atrue%7D%7D</tool_result>
        <relative_workspace_path>/home/rogermt/forgesyte/docs/releases/v0.9.1/FIX_RESULTS_FILE.md</relative_workspace_path>
        <should_read_entire_file>true</should_read_entire_file>
      </tool>
<think>Now I understand both fixes:

**FIX_RELEATIVE_PATHS.md**: This is about fixing the worker to store relative paths instead of full paths in the database. The issue is that:
- Worker currently stores full paths like `data/video_jobs/output/<job_id>.json` in `job.output_path`
- The storage service `load_file()` expects relative paths and prepends `base_dir`
- This causes double prefixing: `data/video_jobs/data/video_jobs/output/<job_id>.json` → 404
- The fix is to make the worker store only relative paths like `output/<job_id>.json`
- This requires changes to:
  1. Worker - store relative paths only
  2. LocalStorageService - ensure it returns relative paths from save_file
  3. Migration - clean up old absolute paths in DB
  4. Regression test - ensure relative paths are stored

**FIX_RESULTS_FILE.md**: This is about fixing the results endpoint that returns 404. The current workaround is to bypass `storage.load_file()` since `job.output_path` contains a full path. However, this is a temporary fix - the proper fix is to implement FIX_RELEATIVE_PATHS.md instead.

Looking at the two documents, FIX_RESULTS_FILE.md is actually a temporary workaround, while FIX_RELEATIVE_PATHS.md is the proper architectural fix. The FIX_RESULTS_FILE.md document even says:

> You fixed the endpoint by bypassing `storage.load_file()`, which works — but it's a workaround, not a clean architecture.

And FIX_RELEATIVE_PATHS.md says:

> **Yes — patch the worker to store relative paths only.**  
> It's the correct architectural choice and prevents future breakage.

So the plan should be:


I'll investigate the codebase to locate the specific files that need modification. This involves tracking down the worker implementation, storage service, and results endpoint to understand their current structure and how they interact. I'll start by searching for these key components to map out the existing implementation.</think>
Now let me explore the relevant codebase to understand the current implementation:
<tool id=call_6ff024cf22a44b8bbfadabb4>
        <tool_name>glob</tool_name><tool_result>%7B%22success%22%3Atrue%2C%22tool_name%22%3A%22glob%22%2C%22params%22%3A%7B%22pattern%22%3A%22**%2Fworker.py%22%2C%22path%22%3A%22%2Fhome%2Frogermt%2Fforgesyte%2Fserver%22%7D%2C%22result%22%3A%22Found%201%20matching%20file(s)%22%7D</tool_result>
        <pattern>**/worker.py</pattern>
        <path>/home/rogermt/forgesyte/server</path>
      </tool>

<tool id=call_a203110d97034c02a867ad51>
        <tool_name>glob</tool_name><tool_result>%7B%22success%22%3Atrue%2C%22tool_name%22%3A%22glob%22%2C%22params%22%3A%7B%22pattern%22%3A%22**%2Fstorage*.py%22%2C%22path%22%3A%22%2Fhome%2Frogermt%2Fforgesyte%2Fserver%22%7D%2C%22result%22%3A%22No%20files%20found%22%7D</tool_result>
        <pattern>**/storage*.py</pattern>
        <path>/home/rogermt/forgesyte/server</path>
      </tool>

<tool id=call_e37a42e4ea074969b7fdd26e>
        <tool_name>glob</tool_name><tool_result>%7B%22success%22%3Atrue%2C%22tool_name%22%3A%22glob%22%2C%22params%22%3A%7B%22pattern%22%3A%22**%2Fvideo*results*.py%22%2C%22path%22%3A%22%2Fhome%2Frogermt%2Fforgesyte%2Fserver%22%7D%2C%22result%22%3A%22No%20files%20found%22%7D</tool_result>
        <pattern>**/video*results*.py</pattern>
        <path>/home/rogermt/forgesyte/server</path>
      </tool>
<think>Let me search more broadly for storage and results-related files:
<tool id=call_70daa1a0b185446b9f61c7dd>
        <tool_name>search_file_content</tool_name><tool_result>%7B%22success%22%3Atrue%2C%22tool_name%22%3A%22search_file_content%22%2C%22params%22%3A%7B%22pattern%22%3A%22class.*Storage.*Service%22%2C%22path%22%3A%22%2Fhome%2Frogermt%2Fforgesyte%2Fserver%2Fapp%22%7D%2C%22result%22%3A%22Found%203%20matches%22%7D</tool_result>
        <pattern>class.*Storage.*Service</pattern>
        <path>/home/rogermt/forgesyte/server/app</path>
      </tool>

<tool id=call_36b0653b28b14d6ea4b06994>
        <tool_name>search_file_content</tool_name><tool_result>%7B%22success%22%3Atrue%2C%22tool_name%22%3A%22search_file_content%22%2C%22params%22%3A%7B%22pattern%22%3A%22%2Fv1%2Fvideo%2Fresults%22%2C%22path%22%3A%22%2Fhome%2Frogermt%2Fforgesyte%2Fserver%2Fapp%22%7D%2C%22result%22%3A%22Found%201%20match%22%7D</tool_result>
        <pattern>/v1/video/results</pattern>
        <path>/home/rogermt/forgesyte/server/app</path>
      </tool>

<tool id=call_9c296387f1a347cca843491b>
        <tool_name>search_file_content</tool_name><tool_result>%7B%22success%22%3Atrue%2C%22tool_name%22%3A%22search_file_content%22%2C%22params%22%3A%7B%22pattern%22%3A%22output_path.*%3D%22%2C%22path%22%3A%22%2Fhome%2Frogermt%2Fforgesyte%2Fserver%2Fapp%22%7D%2C%22result%22%3A%22Found%206%20matches%22%7D</tool_result>
        <pattern>output_path.*=</pattern>
        <path>/home/rogermt/forgesyte/server/app</path>
      </tool>
Good, I found the key files:
1. `/home/rogermt/forgesyte/server/app/services/storage/local_storage.py` - LocalStorageService
2. `/home/rogermt/forgesyte/server/app/workers/worker.py` - Worker with output_path assignment at lines 170, 178
3. `/home/rogermt/forgesyte/server/app/api_routes/routes/job_results.py` - Results endpoint

Let me read these files to understand the current implementation:
<tool id=call_3375f0b690884cbe9a8e0f3d>
        <tool_name>read_file</tool_name><tool_result>%7B%22success%22%3Atrue%2C%22tool_name%22%3A%22read_file%22%2C%22params%22%3A%7B%22relative_workspace_path%22%3A%22%2Fhome%2Frogermt%2Fforgesyte%2Fserver%2Fapp%2Fservices%2Fstorage%2Flocal_storage.py%22%2C%22should_read_entire_file%22%3Atrue%7D%7D</tool_result>
        <relative_workspace_path>/home/rogermt/forgesyte/server/app/services/storage/local_storage.py</relative_workspace_path>
        <should_read_entire_file>true</should_read_entire_file>
      </tool>

<tool id=call_2bf020bae1ec4887bb4f7e52>
        <tool_name>read_file</tool_name><tool_result>%7B%22success%22%3Atrue%2C%22tool_name%22%3A%22read_file%22%2C%22params%22%3A%7B%22relative_workspace_path%22%3A%22%2Fhome%2Frogermt%2Fforgesyte%2Fserver%2Fapp%2Fworkers%2Fworker.py%22%2C%22should_read_entire_file%22%3Atrue%7D%7D</tool_result>
        <relative_workspace_path>/home/rogermt/forgesyte/server/app/workers/worker.py</relative_workspace_path>
        <should_read_entire_file>true</should_read_entire_file>
      </tool>

<tool id=call_a8fc0307d50248d6ab4a8339>
        <tool_name>read_file</tool_name><tool_result>%7B%22success%22%3Atrue%2C%22tool_name%22%3A%22read_file%22%2C%22params%22%3A%7B%22relative_workspace_path%22%3A%22%2Fhome%2Frogermt%2Fforgesyte%2Fserver%2Fapp%2Fapi_routes%2Froutes%2Fjob_results.py%22%2C%22should_read_entire_file%22%3Atrue%7D%7D</tool_result>
        <relative_workspace_path>/home/rogermt/forgesyte/server/app/api_routes/routes/job_results.py</relative_workspace_path>
        <should_read_entire_file>true</should_read_entire_file>
      </tool>
Now I understand the current implementation:

**Current State:**
1. `LocalStorageService.save_file()` at line 35 returns `str(full_path)` - the FULL path
2. `worker.py` line 170-178 stores this full path in `job.output_path`
3. `job_results.py` line 42 calls `storage.load_file(results_path)` which expects a relative path
4. `LocalStorageService.load_file()` at line 48 prepends `BASE_DIR` to the path, causing double prefixing

**The Problem:**
- `save_file()` returns: `/home/rogermt/forgesyte/server/data/video_jobs/output/<job_id>.json`
- This full path is stored in `job.output_path`
- `load_file()` then does: `BASE_DIR / <full_path>` = `data/video_jobs//home/rogermt/forgesyte/server/data/video_jobs/output/<job_id>.json`
- This doesn't exist → 404

**The Fix (from FIX_RELEATIVE_PATHS.md):**
1. Change `LocalStorageService.save_file()` to return `dest_path` (relative) instead of `str(full_path)`
2. Worker already stores whatever `save_file()` returns, so it will now store relative paths
3. `job_results.py` already uses `storage.load_file()`, so it will work correctly
4. Add migration to clean up old absolute paths in DB
5. Add regression test

Let me also check for existing tests and migrations:
<tool id=call_cfa46d31c80f41ea9b812ca2>
        <tool_name>glob</tool_name><tool_result>%7B%22success%22%3Atrue%2C%22tool_name%22%3A%22glob%22%2C%22params%22%3A%7B%22pattern%22%3A%22**%2Fmigrations%2Fversions%2F*.py%22%2C%22path%22%3A%22%2Fhome%2Frogermt%2Fforgesyte%2Fserver%22%7D%2C%22result%22%3A%22Found%203%20matching%20file(s)%22%7D</tool_result>
        <pattern>**/migrations/versions/*.py</pattern>
        <path>/home/rogermt/forgesyte/server</path>
      </tool>

<tool id=call_dde1cf066f7745d08d53c38d>
        <tool_name>glob</tool_name><tool_result>%7B%22success%22%3Atrue%2C%22tool_name%22%3A%22glob%22%2C%22params%22%3A%7B%22pattern%22%3A%22**%2Ftest*worker*.py%22%2C%22path%22%3A%22%2Fhome%2Frogermt%2Fforgesyte%2Fserver%22%7D%2C%22result%22%3A%22Found%201%20matching%20file(s)%22%7D</tool_result>
        <pattern>**/test*worker*.py</pattern>
        <path>/home/rogermt/forgesyte/server</path>
      </tool>

<tool id=call_ab6b7a0a458f4e188c542430>
        <tool_name>search_file_content</tool_name><tool_result>%7B%22success%22%3Atrue%2C%22tool_name%22%3A%22search_file_content%22%2C%22params%22%3A%7B%22pattern%22%3A%22BASE_DIR.*%3D%22%2C%22path%22%3A%22%2Fhome%2Frogermt%2Fforgesyte%2Fserver%2Fapp%22%7D%2C%22result%22%3A%22Found%202%20matches%22%7D</tool_result>
        <pattern>BASE_DIR.*=</pattern>
        <path>/home/rogermt/forgesyte/server/app</path>
      </tool>
Let me check the latest migration and the worker test to understand the current state better:
<tool id=call_d28765de25364a76820231fa>
        <tool_name>read_file</tool_name><tool_result>%7B%22success%22%3Atrue%2C%22tool_name%22%3A%22read_file%22%2C%22params%22%3A%7B%22relative_workspace_path%22%3A%22%2Fhome%2Frogermt%2Fforgesyte%2Fserver%2Fapp%2Fmigrations%2Fversions%2F003_add_plugin_id_and_tool.py%22%2C%22should_read_entire_file%22%3Atrue%7D%7D</tool_result>
        <relative_workspace_path>/home/rogermt/forgesyte/server/app/migrations/versions/003_add_plugin_id_and_tool.py</relative_workspace_path>
        <should_read_entire_file>true</should_read_entire_file>
      </tool>

<tool id=call_c116fc3417ec46aa913f5832>
        <tool_name>read_file</tool_name><tool_result>%7B%22success%22%3Atrue%2C%22tool_name%22%3A%22read_file%22%2C%22params%22%3A%7B%22relative_workspace_path%22%3A%22%2Fhome%2Frogermt%2Fforgesyte%2Fserver%2Ftests%2Fapp%2Fworkers%2Ftest_worker.py%22%2C%22should_read_entire_file%22%3Atrue%7D%7D</tool_result>
        <relative_workspace_path>/home/rogermt/forgesyte/server/tests/app/workers/test_worker.py</relative_workspace_path>
        <should_read_entire_file>true</should_read_entire_file>
      </tool>
Now I have a complete picture. Let me check if there are any other places that use `save_file()` or `load_file()` to understand the impact:
<tool id=call_b6031e5fea924b7091e7a1e2>
        <tool_name>search_file_content</tool_name><tool_result>%7B%22success%22%3Atrue%2C%22tool_name%22%3A%22search_file_content%22%2C%22params%22%3A%7B%22pattern%22%3A%22%5C%5C.save_file%5C%5C(%22%2C%22path%22%3A%22%2Fhome%2Frogermt%2Fforgesyte%2Fserver%2Fapp%22%7D%2C%22result%22%3A%22Found%202%20matches%22%7D</tool_result>
        <pattern>\.save_file\(</pattern>
        <path>/home/rogermt/forgesyte/server/app</path>
      </tool>

<tool id=call_7e9ec5ac963c47998ab03c58>
        <tool_name>search_file_content</tool_name><tool_result>%7B%22success%22%3Atrue%2C%22tool_name%22%3A%22search_file_content%22%2C%22params%22%3A%7B%22pattern%22%3A%22%5C%5C.load_file%5C%5C(%22%2C%22path%22%3A%22%2Fhome%2Frogermt%2Fforgesyte%2Fserver%2Fapp%22%7D%2C%22result%22%3A%22Found%202%20matches%22%7D</tool_result>
        <pattern>\.load_file\(</pattern>
        <path>/home/rogermt/forgesyte/server/app</path>
      </tool>
Let me check the video_submit.py to see how it uses save_file:
<tool id=call_bc1e557cc2644ede913d73ce>
        <tool_name>read_file</tool_name><tool_result>%7B%22success%22%3Atrue%2C%22tool_name%22%3A%22read_file%22%2C%22params%22%3A%7B%22relative_workspace_path%22%3A%22%2Fhome%2Frogermt%2Fforgesyte%2Fserver%2Fapp%2Fapi_routes%2Froutes%2Fvideo_submit.py%22%2C%22should_read_entire_file%22%3Atrue%7D%7D</tool_result>
        <relative_workspace_path>/home/rogermt/forgesyte/server/app/api_routes/routes/video_submit.py</relative_workspace_path>
        <should_read_entire_file>true</should_read_entire_file>
      </tool>
Now I have a complete understanding of the codebase. Let me create a comprehensive plan:

## Current State Analysis:

### Files to modify:
1. **`server/app/services/storage/local_storage.py`** - Change `save_file()` to return relative path
2. **`server/app/migrations/versions/004_fix_output_paths_relative.py`** - NEW migration to clean up old absolute paths
3. **`server/tests/app/workers/test_worker.py`** - Update tests to expect relative paths, add regression test

### Files that will work automatically after fix:
1. **`server/app/workers/worker.py`** - Already stores whatever `save_file()` returns
2. **`server/app/api_routes/routes/job_results.py`** - Already uses `storage.load_file()` correctly

### Impact analysis:
- `video_submit.py` line 57: `storage.save_file()` returns full path, but it's NOT stored in DB - only `input_path` (relative) is stored. So this is fine.
- `worker.py` line 170: `storage.save_file()` returns full path, stored in `job.output_path` - THIS IS THE BUG
- `worker.py` line 151: `storage.load_file(job.input_path)` - `job.input_path` is already relative, so this works
- `job_results.py` line 44: `storage.load_file(job.output_path)` - `job.output_path` is full path, causes double prefixing

## The Fix:

### 1. Change `LocalStorageService.save_file()` to return relative path
**File**: `server/app/services/storage/local_storage.py`
**Line**: 35
**Change**: `return str(full_path)` → `return dest_path`

### 2. Create migration to clean up old absolute paths
**File**: `server/app/migrations/versions/004_fix_output_paths_relative.py` (NEW)
**Purpose**: Convert existing absolute paths in `jobs.output_path` to relative paths


**Logic**: Identify absolute paths by checking for leading slash or containing "video_jobs", then strip the prefix to extract the relative path

### 3. Update worker tests
**File**: `server/tests/app/workers/test_worker.py`
**Changes**:
- Update mock expectations from full paths to relative paths
- Add new regression test to verify only relative paths are stored

I'll verify the test expectations and ensure the new regression test covers the path conversion logic comprehensively.</think>
Now let me check the existing tests to see what they expect:
<tool id=call_ae80100e16d841578c47c7a2>
        <tool_name>search_file_content</tool_name><tool_result>%7B%22success%22%3Atrue%2C%22tool_name%22%3A%22search_file_content%22%2C%22params%22%3A%7B%22pattern%22%3A%22save_file%5C%5C.return_value%22%2C%22path%22%3A%22%2Fhome%2Frogermt%2Fforgesyte%2Fserver%2Ftests%22%7D%2C%22result%22%3A%22Found%205%20matches%22%7D</tool_result>
        <pattern>save_file\.return_value</pattern>
        <path>/home/rogermt/forgesyte/server/tests</path>
      </tool>
<think>Now I have all the information I need. Let me create a comprehensive plan. I'm confident about this implementation because:

1. I've identified all the files that need to be changed
2. I understand the root cause and the fix
3. I've analyzed the impact on all usages of `save_file()` and `load_file()`
4. I know what tests need to be updated
5. I know what migration needs to be created

Let me now create a detailed implementation plan.</think>
Based on my analysis of the codebase and the two fix documents, I have a clear understanding of the issues. Here's my implementation plan:

---

## **Analysis Summary**

Looking at both fix documents:

**FIX_RESULTS_FILE.md** describes a **temporary workaround** (bypassing `storage.load_file()`) to fix the 404 error.

**FIX_RELEATIVE_PATHS.md** describes the **proper architectural fix** - making the worker store relative paths instead of full paths.

**My recommendation**: Implement FIX_RELEATIVE_PATHS.md (the proper fix) instead of the workaround. This is the correct long-term solution.

---

## **Root Cause**

Current flow:
1. `LocalStorageService.save_file()` returns **full path**: `/home/.../data/video_jobs/output/<job_id>.json`
2. Worker stores this full path in `job.output_path`
3. `job_results.py` calls `storage.load_file(job.output_path)` 
4. `load_file()` prepends `BASE_DIR` → double prefixing → file not found

**The Fix**: Change step 1 to return **relative path** only: `output/<job_id>.json`

---

## **Implementation Plan**

### **Files to Modify**

1. **`server/app/services/storage/local_storage.py`**
   - Line 35: Change `return str(full_path)` → `return dest_path`
   - This makes `save_file()` return relative paths only

2. **`server/app/migrations/versions/004_fix_output_paths_relative.py`** (NEW)
   - Create new migration to clean up existing absolute paths in `jobs.output_path`
   - Convert paths like `data/video_jobs/output/<id>.json` → `output/<id>.json`

3. **`server/tests/app/workers/test_worker.py`**
   - Update 5 mock expectations from full paths to relative paths
   - Add new regression test to ensure only relative paths are stored

### **Files That Work Automatically**

- `server/app/workers/worker.py` - Already stores whatever `save_file()` returns
- `server/app/api_routes/routes/job_results.py` - Already uses `storage.load_file()` correctly
- `server/app/api_routes/routes/video_submit.py` - Uses `save_file()` but doesn't store the return value

---

## **Detailed Changes**

### 1. LocalStorageService.save_file()

**Current:**
```python
return str(full_path)  # Returns full path
```

**After:**
```python
return dest_path  # Returns relative path only
```

### 2. Migration (NEW FILE)

**File**: `server/app/migrations/versions/004_fix_output_paths_relative.py`

**Logic:**
- Query all jobs with `output_path`
- If path starts with `/` or contains `video_jobs`, extract relative part
- Update `output_path` to relative path

### 3. Test Updates

**Update 5 existing test mocks:**
```python
# Before
mock_storage.save_file.return_value = "/data/video_jobs/output/test.json"

# After
mock_storage.save_file.return_value = "output/test.json"
```

**Add new regression test:**
```python
def test_worker_stores_relative_output_path_only(test_engine, session):
    """Ensure worker stores relative paths, not absolute paths."""
    # Create job, mock storage to return relative path
    # Verify job.output_path is relative (doesn't start with /, doesn't contain video_jobs)
```

---

## **Questions Before Implementation**

I'm **95% confident** in this plan, but I have a few questions:

1. **Migration Scope**: Should the migration delete old jobs (like migration 003 does) or just fix their paths? I recommend fixing paths to preserve data.

2. **BASE_DIR Path**: The `BASE_DIR` is `Path("./data/video_jobs")`. This is relative to the current working directory. Is this intentional, or should it be an absolute path? (This affects whether `load_file()` will work correctly from different directories.)

3. **Test Coverage**: Should I add integration tests that actually write files to disk and verify the paths work end-to-end, or are unit tests sufficient?

4. **Backward Compatibility**: Are there any existing jobs in production databases that need to be migrated? If so, we should test the migration on real data.

---

## **Next Steps**

Once you confirm the answers to these questions, I'll:
1. Update `LocalStorageService.save_file()` to return relative paths
2. Create migration 004 to clean up old absolute paths
3. Update all affected tests
4. Run the full test suite to verify everything works
5. Run execution governance verification

Should I proceed with the implementation, or do you need clarification on any of these points?


Questions Before Implementation
I'm 95% confident in this plan, but I have a few questions:

Migration Scope: Should the migration delete old jobs (like migration 003 does) or just fix their paths? I recommend fixing paths to preserve data.

BASE_DIR Path: The BASE_DIR is Path("./data/video_jobs"). This is relative to the current working directory. Is this intentional, or should it be an absolute path? (This affects whether load_file() will work correctly from different directories.)

Test Coverage: Should I add integration tests that actually write files to disk and verify the paths work end-to-end, or are unit tests sufficient?

Backward Compatibility: Are there any existing jobs in production databases that need to be migrated? If so, we should test the migration on real data.



Alright — now that you’ve clarified the version plan:

- **v0.9.1 = Video only (new job system)**
- **v0.9.2 = Image migration to new job system**
- **v1.0.0 = First supported release**

…we can answer your questions cleanly and without mixing the two systems.

Let’s go through each question with the correct answer for **your actual migration path**.

---

# ⭐ 1. Migration Scope  
### **Q: Should the migration delete old jobs or fix their paths?**

Since:

- v0.9.1 introduces the new video job system  
- v0.9.2 will migrate image jobs  
- **There is no previous supported release**  
- **There is no production data to preserve**

### ✅ Correct answer:
**Do NOT delete jobs. Do NOT fix paths.  
Just drop the old job system entirely.**

Why?

Because:

- The old job system (TaskProcessor + JobManagementService) is being replaced  
- The old job table is irrelevant  
- No one is depending on old job data  
- v1.0.0 will only use the new job system  

### ✔ Migration should simply:
- Drop the old job table  
- Create the new unified Job table  
- Store relative paths only  
- No path fixing required  

This is the cleanest possible migration.

---

# ⭐ 2. BASE_DIR Path  
### **Q: Should BASE_DIR be absolute or relative?**

Your current:

```python
BASE_DIR = Path("./data/video_jobs")
```

This is dangerous because:

- CWD changes between dev, Docker, Kaggle, VSCode, systemd  
- Worker and API may run from different directories  
- Tests run from different roots  

### ✅ Correct answer:
**BASE_DIR must be absolute.**

Use:

```python
BASE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "video_jobs"
```

Or environment-based:

```python
BASE_DIR = Path(os.getenv("VIDEO_STORAGE_DIR", "./data/video_jobs")).resolve()
```

### Why?
Because:

- Worker → always absolute  
- API → always absolute  
- Tests → always absolute  
- No surprises  
- No “file not found” due to CWD differences  

---

# ⭐ 3. Test Coverage  
### **Q: Should we add integration tests that write files to disk?**

Since:

- v0.9.1 introduces the new job system  
- v0.9.2 will migrate image jobs  
- v1.0.0 will rely entirely on this system  

### ✅ Correct answer:
**Yes — you need at least one full end‑to‑end integration test.**

Unit tests alone are not enough.

You need to test:

- Worker writes JSON  
- Storage resolves paths  
- Plugin runs correctly  
- Endpoint loads JSON  
- Everything works together  

You already asked for the E2E test — that’s exactly the right move.

---

# ⭐ 4. Backward Compatibility  
### **Q: Are there any existing jobs in production that need migration?**

You said:

> None, we have no previous supported release. v1.0.0 will be first release.

### ✅ Correct answer:
**No backward compatibility needed.**

This means:

- No path fixing  
- No fallback logic  
- No pipeline_id migration  
- No TaskProcessor migration  
- No JobManagementService migration  
- No legacy endpoints to preserve  

You are free to delete the old system entirely.

---

# ⭐ 5. Old Video Endpoints  
### **Q: What happens to old video endpoints when we move to unified jobs?**

You currently have:

```
/v1/video/status/{id}
/v1/video/results/{id}
```

These were temporary endpoints for v0.9.1.

### In v0.9.2 (image migration):
- Keep them temporarily  
- Add unified endpoint `/v1/jobs/{id}`  
- Begin migrating UI to unified endpoint  

### In v1.0.0:
- Remove `/v1/video/status`  
- Remove `/v1/video/results`  
- Remove `/jobs/...` (old image system)  
- Keep only:

```
POST /v1/jobs
GET /v1/jobs/{id}
```

### Final answer:
**Old video endpoints are temporary and will be removed in v1.0.0.**

---

# ⭐ Final Summary (for v0.9.1 → v0.9.2 → v1.0.0)

| Topic | Correct Action |
|-------|----------------|
| Migration scope | Drop old job system entirely |
| BASE_DIR | Use absolute path |
| Tests | Unit + full E2E tests required |
| Backward compatibility | None needed |
| Old video endpoints | Temporary; remove in v1.0.0 |
| Unified endpoint | `/v1/jobs/{id}` for everything |

---

If you want, I can now generate:

### 🔧 The unified `/v1/jobs/{id}` endpoint  
### 🔧 The migration script for v0.9.2  
### 🔧 The patch to delete the old job system  
### 🔧 The patch to remove old video endpoints  
### 🔧 The final directory structure for v1.0.0  

Just tell me what you want next.