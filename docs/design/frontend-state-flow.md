# Frontend State Flow Analysis

**Purpose:** Document all frontend features, state dependencies, and polling behavior to identify issues before making changes.

---

## State Summary

### Global State (App.tsx)

| State Variable | Type | Purpose | Initialized |
|----------------|------|---------|-------------|
| `viewMode` | `"stream" \| "upload" \| "jobs" \| "video-upload" \| "video-stream"` | Current view | `"stream"` |
| `selectedPlugin` | `string` | Selected plugin ID | `""` |
| `selectedTools` | `string[]` | Selected tool IDs | `[]` |
| `lockedTools` | `string[] \| null` | Tools locked after upload | `null` |
| `videoFile` | `File \| null` | Uploaded video file | `null` |
| `selectedJob` | `Job \| null` | Job selected from JobList | `null` |
| `uploadResult` | `Job \| null` | Job from image/video upload | `null` |
| `isUploading` | `boolean` | Upload in progress | `false` |
| `manifest` | `PluginManifest \| null` | Plugin manifest | `null` |
| `manifestError` | `string \| null` | Manifest load error | `null` |
| `manifestLoading` | `boolean` | Manifest loading | `false` |
| `streamEnabled` | `boolean` | Camera streaming active | `false` |

### Component-Local State

| Component | State | Type | Initialized |
|-----------|-------|------|-------------|
| `PluginSelector` | `plugins` | `Plugin[]` | `[]` |
| `PluginSelector` | `loading` | `boolean` | `true` |
| `PluginSelector` | `error` | `string \| null` | `null` |
| `JobList` | `jobs` | `Job[]` | `[]` |
| `JobList` | `loading` | `boolean` | `true` |
| `JobList` | `error` | `string \| null` | `null` |
| `JobStatus` | `pollProgress` | `number \| null` | `null` |
| `JobStatus` | `pollStatus` | `Status` | **`"pending"`** |
| `JobStatus` | `pollError` | `string \| null` | `null` |

---

## Feature Flows

### 1. Plugins Loading

**Trigger:** App mounts, PluginSelector renders

```
PluginSelector mount
  └─ useEffect([]) → apiClient.getPlugins()
       └─ GET /v1/plugins
            ├─ SUCCESS → setPlugins(data), setLoading(false)
            └─ FAIL → setError(msg), setPlugins([])
```

**Dependencies:** None (runs on mount)

**Polling Required:** NO - one-time fetch

**State Changes:**
- `PluginSelector.plugins` populated
- `PluginSelector.loading` → `false`
- Auto-selects first plugin → calls `onPluginChange(plugins[0].name)`
  - This triggers `App.selectedPlugin` update

---

### 2. Tools Selection

**Trigger:** `selectedPlugin` changes

```
selectedPlugin change (App.tsx)
  └─ useEffect([selectedPlugin]) → loadManifest()
       └─ GET /v1/plugins/{pluginId}/manifest
            ├─ SUCCESS → setManifest(data)
            │    └─ manifest change triggers toolList computation
            │         └─ Auto-select first tool → setSelectedTools([toolList[0]])
            └─ FAIL → setManifestError(msg), setManifest(null)
```

**Dependencies:** 
- Requires `selectedPlugin` to be set
- Requires server running

**Polling Required:** NO - one-time fetch per plugin change

**State Changes:**
- `App.manifest` populated
- `App.manifestLoading` → `false`
- `App.selectedTools` auto-populated with first tool
- `App.selectedJob` → `null` (reset on plugin change)
- `App.uploadResult` → `null` (reset on plugin change)
- `App.lockedTools` → `null` (reset on plugin change)

---

### 3. Job List

**Trigger:** `viewMode === "jobs"`

```
viewMode === "jobs" → JobList renders
  └─ useEffect([]) → apiClient.listJobs()
       └─ GET /v1/jobs?limit=10&skip=0
            ├─ SUCCESS → setJobs(data), setLoading(false)
            └─ FAIL → setError(msg), setJobs([])
```

**Dependencies:**
- Requires server running
- Does NOT require plugin to be loaded

**Polling Required:** NO - one-time fetch on mount

**State Changes:**
- `JobList.jobs` populated
- `JobList.loading` → `false`

**User Interaction:**
- User clicks job → `onJobSelect(job)` → `App.setSelectedJob(job)`

---

### 4. Job Info (JobStatus)

**Trigger:** `selectedJob` or `uploadResult` set with `job_id`

**Three Polling Mechanisms:**

#### 4a. App.tsx `selectedJob` Polling (Line 219-237)

```typescript
useEffect(() => {
  if (!selectedJob?.job_id) return;
  if (selectedJob?.status === "completed" || selectedJob?.status === "failed") return;
  
  const interval = setInterval(async () => {
    const job = await apiClient.getJob(selectedJob.job_id);
    setSelectedJob(job);
  }, 1000);
  
  return () => clearInterval(interval);
}, [selectedJob?.job_id, selectedJob?.status]);
```

**Stops When:** `selectedJob.status` is `"completed"` or `"failed"`

#### 4b. App.tsx `uploadResult` Polling (Line 243-261)

```typescript
useEffect(() => {
  if (!uploadResult?.job_id) return;
  if (uploadResult?.status === "completed" || uploadResult?.status === "failed") return;
  
  const interval = setInterval(async () => {
    const job = await apiClient.getJob(uploadResult.job_id);
    setUploadResult(job);
  }, 1000);
  
  return () => clearInterval(interval);
}, [uploadResult?.job_id, uploadResult?.status]);
```

**Stops When:** `uploadResult.status` is `"completed"` or `"failed"`

#### 4c. JobStatus.tsx HTTP Polling (Line 39-77)

```typescript
const [pollStatus, setPollStatus] = useState<Status>("pending"); // ALWAYS "pending" on mount!

useEffect(() => {
  if (!jobId) return;
  if (pollStatus === "failed") return;
  if (pollStatus === "completed") return;
  
  // Skip if WebSocket connected
  if (isConnected && wsStatus !== "completed") return;
  
  const poll = async () => {
    const job = await apiClient.getJob(jobId);
    setPollStatus(job.status as Status);
    // ... continues polling if not completed
  };
  
  poll();
}, [jobId, isConnected, wsStatus, pollStatus]);
```

**Stops When:** `pollStatus` is `"completed"` or `"failed"`

**BUG:** `pollStatus` initializes to `"pending"` on EVERY mount/remount!
- If job is already completed, but JobStatus remounts (e.g., view mode switch), polling restarts
- This causes duplicate polling even for completed jobs

---

### 5. Image Upload

**Trigger:** User selects image file in Upload mode

```
handleFileUpload (App.tsx:310-345)
  └─ Lock tools → setLockedTools(selectedTools)
  └─ Pause streaming → setStreamEnabled(false)
  └─ setIsUploading(true)
  └─ POST /v1/image/submit?plugin_id=X&tool=Y
       └─ Returns { job_id }
  └─ apiClient.pollJob(job_id) // BLOCKING until complete!
       └─ GET /v1/jobs/{job_id} repeatedly until completed/failed
  └─ setSelectedJob(job)
  └─ setIsUploading(false)
```

**Dependencies:**
- Requires `selectedPlugin` set
- Requires `selectedTools` not empty
- Requires server running

**Polling Required:** YES - `pollJob()` in handler (blocking)

**State Changes:**
- `App.lockedTools` → selected tools (locked)
- `App.isUploading` → `true` then `false`
- `App.selectedJob` → job object (from pollJob)
- `App.uploadResult` → NOT SET in image upload!

**Note:** Image upload uses `pollJob()` which blocks until completion.
The job is already completed when `setSelectedJob()` is called.

---

### 6. Video Upload

**Trigger:** User clicks "Run Job" in VideoUpload component

```
handleRunJob (VideoUpload.tsx)
  └─ POST /v1/video/upload → returns { video_path }
  └─ onStartStreaming OR onRunJob callback

handleRunVideoJob (App.tsx:456-476)
  └─ setLockedTools(lockedTools)
  └─ POST /v1/video/job
       └─ Returns { job_id }
  └─ const initialJobState = { job_id, status: "pending", ... }
  └─ setUploadResult(initialJobState)  // status: "pending"
  └─ setSelectedJob(initialJobState)   // status: "pending"
```

**Dependencies:**
- Requires `selectedPlugin` set
- Requires `selectedTools` not empty
- Requires server running

**Polling Required:** YES - both App polling AND JobStatus polling

**State Changes:**
- `App.lockedTools` → locked tools
- `App.uploadResult` → `{ job_id, status: "pending" }`
- `App.selectedJob` → `{ job_id, status: "pending" }`

**Polling Chain:**
1. `App.selectedJob` polling starts (status="pending")
2. `App.uploadResult` polling starts (status="pending")
3. `JobStatus` mounts with `pollStatus="pending"` → starts HTTP polling
4. **THREE concurrent polling loops for same job!**

---

### 7. Run Job

**Trigger:** User clicks job in JobList (Jobs view)

```
JobList onClick → onJobSelect(job)
  └─ setSelectedJob(job)
       └─ Triggers App.selectedJob polling IF status not terminal
       └─ JobStatus mounts with pollStatus="pending"
            └─ Triggers JobStatus HTTP polling (BUG!)
```

**Dependencies:**
- Requires JobList loaded
- Requires server running

**Polling Required:** Only if job status is not terminal

**State Changes:**
- `App.selectedJob` → clicked job

**BUG SCENARIO:**
1. User uploads video → job completes
2. User navigates away from video-upload view
3. User clicks "Jobs" button
4. User clicks the completed job
5. `JobStatus` mounts fresh with `pollStatus="pending"`
6. **Polling starts even though job is already completed!**

---

### 8. Download JSON

**Trigger:** User clicks "Download Full JSON" in ResultsPanel

```
ResultsPanel onClick
  └─ job.result_url exists?
       └─ window.open(job.result_url, "_blank")
            └─ GET /v1/jobs/{job_id}/result
                 └─ Returns JSON file download
```

**Dependencies:**
- Requires `job.result_url` to be set
- Requires server running
- Requires job to be completed

**Polling Required:** NO - direct download

**State Changes:** None

---

## Polling Analysis

### Current Polling Locations

| Location | Condition | Interval | Stops When |
|----------|-----------|----------|------------|
| App.tsx selectedJob | `selectedJob.status` not terminal | 1000ms | status=completed/failed |
| App.tsx uploadResult | `uploadResult.status` not terminal | 1000ms | status=completed/failed |
| JobStatus.tsx | `pollStatus` not terminal | 2000ms | pollStatus=completed/failed |

### Polling Overlap Scenarios

#### Scenario A: Video Upload (Worst Case)
```
1. handleRunVideoJob sets:
   - uploadResult.status = "pending"
   - selectedJob.status = "pending"

2. THREE polling loops start:
   - App.selectedJob polling (1000ms)
   - App.uploadResult polling (1000ms)
   - JobStatus.pollStatus polling (2000ms)

3. Each makes separate GET /v1/jobs/{id} calls
4. Total: ~3 requests per second for same job!
```

#### Scenario B: Job List Selection of Completed Job (BUG)
```
1. User clicks completed job in JobList
2. setSelectedJob(completedJob) - status = "completed"
3. App.selectedJob polling SKIPPED (status is terminal) ✓
4. JobStatus mounts with pollStatus="pending" ✗
5. JobStatus polling starts for COMPLETED job!
6. First poll call fetches job → status="completed"
7. pollStatus updated → polling finally stops
```

---

## Root Causes

### 1. JobStatus State Initialization Bug ✅ FIXED
**File:** `web-ui/src/components/JobStatus.tsx:23`
```typescript
const [pollStatus, setPollStatus] = useState<Status>("pending");
```

**Problem:** Always initializes to `"pending"`, even when job is already completed.

**Fix:** Pass `initialStatus` prop from parent:
```typescript
// App.tsx
<JobStatus jobId={job.job_id} initialStatus={job.status} />

// JobStatus.tsx
const [pollStatus, setPollStatus] = useState<Status>(initialStatus || "pending");
```

**Status:** Fixed in PR #364, Issue #363

### 2. JobList Fetch-Once Bug 🔴 OPEN
**File:** `web-ui/src/components/JobList.tsx`
```typescript
useEffect(() => {
    const loadJobs = async () => { ... };
    loadJobs();
}, []);  // Only runs ONCE on mount
```

**Problem:** If network error occurs on first fetch, JobList shows "failed to fetch" and never retries. User must refresh page.

**Fix:** Add `viewMode` prop and re-fetch when switching to Jobs view:
```typescript
useEffect(() => {
  if (viewMode !== 'jobs') return;
  loadJobs();
}, [viewMode]);
```

**Status:** Open - Issue #365

### 3. Duplicate Polling State
**Problem:** Both `selectedJob` and `uploadResult` track job state separately, causing duplicate polling.

**Fix:** Consolidate to single job state, or derive one from the other.

### 3. Polling in Multiple Layers
**Problem:** App.tsx polls AND JobStatus.tsx polls. No coordination.

**Fix:** JobStatus should only poll if parent is not polling.

---

## Recommendations

### Short-term Fix (Minimal Change)
1. Add `initialStatus` prop to `JobStatus`
2. Initialize `pollStatus` from prop instead of hardcoded `"pending"`
3. Pass `selectedJob.status` and `uploadResult.status` from App.tsx

### Medium-term Refactor
1. Consolidate `selectedJob` and `uploadResult` into single state
2. Move polling logic to custom hook
3. Add polling coordinator to prevent duplicate requests

### Long-term Architecture
1. Consider WebSocket-only updates for job status
2. Remove HTTP polling entirely once WebSocket is reliable
3. Implement proper state management (Context/Redux/Zustand)

---

## State Dependencies Graph

```
┌─────────────────────────────────────────────────────────────┐
│                         App.tsx                              │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐   │
│  │ viewMode    │───►│ renders      │    │ selectedPlugin│   │
│  └─────────────┘    │ - JobList    │    └───────┬───────┘   │
│         │           │ - VideoUpload│            │           │
│         │           │ - JobStatus  │            ▼           │
│         │           └──────────────┘    ┌───────────────┐   │
│         │                               │ manifest      │   │
│         │                               └───────┬───────┘   │
│         │                                       │           │
│         │                                       ▼           │
│         │                               ┌───────────────┐   │
│         │                               │ selectedTools │   │
│         │                               └───────┬───────┘   │
│         │                                       │           │
│         ▼                                       ▼           │
│  ┌─────────────┐                        ┌───────────────┐   │
│  │ selectedJob │◄───────────────────────│ lockedTools   │   │
│  └──────┬──────┘                        └───────────────┘   │
│         │                                                   │
│         │           ┌──────────────┐                        │
│         └──────────►│ uploadResult │                        │
│                     └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │    JobStatus.tsx      │
              │  ┌─────────────────┐  │
              │  │ pollStatus="pending" │◄── BUG: Always "pending"!
              │  └─────────────────┘  │
              └───────────────────────┘
```

---

## Action Items

1. **[x] Fix JobStatus initialStatus** - Add prop, pass from parent ✅ PR #364
2. **[ ] Fix JobList fetch-once bug** - Re-fetch on viewMode change (Issue #365)
3. **[ ] Add tests for polling stop conditions** - TDD approach
4. **[x] Document polling behavior** - This document
5. **[ ] Consider consolidating job state** - Future refactor
