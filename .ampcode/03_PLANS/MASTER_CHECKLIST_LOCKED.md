# Implementation Checklist: Job Pipeline Cleanup (#146)

**Issue**: [#146](https://github.com/rogermt/forgesyte/issues/146)  
**Branch**: `refactor/web-ui-job-pipeline-cleanup`  
**Status**: Ready for Implementation  

---

## Pre-Implementation Approval ✋

**STOP HERE** — Confirm answers to these questions before proceeding:

### Questions Requiring Approval

- [ ] **Plugin Selection**: How do users pick a plugin now?
  - [ ] A) Dropdown in AnalyzePage using `apiClient.listPlugins()`
  - [ ] B) Keep a minimal `PluginSelector` component
  - [ ] C) Other (specify): _____________

- [ ] **Result Rendering**: How should `ResultsPanel` display results?
  - [ ] A) Generic JSON pretty-print
  - [ ] B) Simple card layout (key/value pairs)
  - [ ] C) Keep plugin-specific renderers (OCR, YOLO, etc.)
  - [ ] D) Other (specify): _____________

- [ ] **Video Overlay**: Where does overlay rendering happen?
  - [ ] A) Inside `VideoTracker` component
  - [ ] B) In a separate `VideoOverlay` component
  - [ ] C) Not implemented yet (TODO)
  - [ ] D) Other (specify): _____________

- [ ] **Error Retry**: What should "Retry" button do?
  - [ ] A) Re-process same file/frame
  - [ ] B) Clear error and wait for new upload
  - [ ] C) Optional (callback passed by parent)
  - [ ] D) Other (specify): _____________

- [ ] **Testing Framework**: Confirm test setup
  - [ ] A) Vitest + React Testing Library (current setup)
  - [ ] B) Jest + Enzyme (different setup)
  - [ ] C) Other (specify): _____________

**Approver**: ________________  
**Date**: ________________  
**Approved**: [ ] Yes  [ ] No

---

## Phase 1: Preparation (15 min)

- [ ] Read all documents in `/home/rogermt/forgesyte/.ampcode/`:
  - [ ] `WEB-UI_ISSUE_146.md` (main plan)
  - [ ] `MIGRATION_PLAN.md` (detailed steps)
  - [ ] `ARCHITECTURE_BEFORE_AFTER.md` (diagrams)
  - [ ] `migrate_to_job_pipeline.sh` (helper script)

- [ ] Run preparation script:
  ```bash
  cd /home/rogermt/forgesyte
  chmod +x .ampcode/migrate_to_job_pipeline.sh
  ./.ampcode/migrate_to_job_pipeline.sh
  ```

- [ ] Document findings:
  - [ ] Files to delete: ___________
  - [ ] Files to update: ___________
  - [ ] Missing files: ___________

- [ ] Verify branch is clean:
  ```bash
  git status  # Should show clean working directory
  ```

---

## Phase 2: File Deletions (10 min)

### 2.1 Delete `ToolSelector.tsx`

- [ ] Check current location:
  ```bash
  find web-ui -name "ToolSelector.tsx" -type f
  ```

- [ ] View file before deletion (confirm it's the right one):
  ```bash
  cat web-ui/src/components/ToolSelector.tsx
  ```

- [ ] Delete via git:
  ```bash
  git rm web-ui/src/components/ToolSelector.tsx
  ```

- [ ] Remove imports from:
  - [ ] `web-ui/src/pages/AnalyzePage.tsx` (or wherever it's imported)
  - [ ] `web-ui/src/pages/__tests__/AnalyzePage.test.tsx` (if exists)

- [ ] Search for any remaining references:
  ```bash
  rg "ToolSelector" web-ui/src/
  # Should return: 0 results
  ```

### 2.2 Delete `detectToolType.ts`

- [ ] Check current location:
  ```bash
  find web-ui -name "detectToolType.ts" -type f
  ```

- [ ] View file before deletion:
  ```bash
  cat web-ui/src/utils/detectToolType.ts
  ```

- [ ] Delete via git:
  ```bash
  git rm web-ui/src/utils/detectToolType.ts
  ```

- [ ] Remove imports from:
  - [ ] `web-ui/src/components/ResultsPanel.tsx`
  - [ ] Any test files

- [ ] Remove branching logic from `ResultsPanel.tsx`:
  - [ ] Find: `if (toolType === "ocr")`
  - [ ] Find: `if (toolType === "yolo")`
  - [ ] Find: `if (toolType === ...)`
  - [ ] Replace with: Generic result display

- [ ] Search for remaining references:
  ```bash
  rg "detectToolType" web-ui/src/
  # Should return: 0 results
  ```

### 2.3 Delete `toolRunner.ts`

- [ ] Check current location:
  ```bash
  find web-ui -name "toolRunner.ts" -type f
  find web-ui -name "runTool.ts" -type f
  ```

- [ ] View file before deletion:
  ```bash
  cat web-ui/src/api/toolRunner.ts  # adjust path if different
  ```

- [ ] Delete via git:
  ```bash
  git rm web-ui/src/api/toolRunner.ts
  ```

- [ ] Remove imports from:
  - [ ] `web-ui/src/components/UploadPanel.tsx`
  - [ ] `web-ui/src/components/VideoTracker.tsx` (if exists)
  - [ ] Any test files

- [ ] Search for remaining references:
  ```bash
  rg "runTool\(" web-ui/src/
  # Should return: 0 results
  ```

- [ ] Verify `apiClient` has these methods:
  ```bash
  rg "analyzeImage|pollJob" web-ui/src/api/apiClient.ts
  # Should show both defined
  ```

---

## Phase 3: Add New Components (20 min)

### 3.1 Create `JobStatusIndicator.tsx`

- [ ] Create file:
  ```bash
  touch web-ui/src/components/JobStatusIndicator.tsx
  ```

- [ ] Copy code from `WEB-UI_ISSUE_146.md` section "2. JobStatusIndicator component"

- [ ] Verify syntax:
  ```bash
  cd web-ui
  npm run type-check -- src/components/JobStatusIndicator.tsx
  ```

- [ ] Create test file:
  ```bash
  touch web-ui/src/components/__tests__/JobStatusIndicator.test.tsx
  ```

- [ ] Copy test code from `MIGRATION_PLAN.md` or write your own

- [ ] Run new tests:
  ```bash
  npm run test -- --run src/components/__tests__/JobStatusIndicator.test.tsx
  # Should pass
  ```

### 3.2 Create `JobError.tsx`

- [ ] Create file:
  ```bash
  touch web-ui/src/components/JobError.tsx
  ```

- [ ] Copy code from `WEB-UI_ISSUE_146.md` section "3. JobError component"

- [ ] Verify syntax:
  ```bash
  npm run type-check -- src/components/JobError.tsx
  ```

- [ ] Create test file:
  ```bash
  touch web-ui/src/components/__tests__/JobError.test.tsx
  ```

- [ ] Write tests (similar to JobStatusIndicator)

- [ ] Run new tests:
  ```bash
  npm run test -- --run src/components/__tests__/JobError.test.tsx
  # Should pass
  ```

---

## Phase 4: Update Existing Components (30 min)

### 4.1 Update `UploadPanel.tsx`

- [ ] Open file:
  ```bash
  code web-ui/src/components/UploadPanel.tsx
  ```

- [ ] Find the old execution code:
  ```tsx
  // OLD:
  const result = await runTool(selectedPluginId, { file });
  ```

- [ ] Replace with new job pipeline code:
  ```tsx
  // NEW:
  const { job_id } = await apiClient.analyzeImage(file, selectedPluginId);
  const job = await apiClient.pollJob(job_id);
  setJob(job);
  ```

- [ ] Update imports:
  - [ ] Remove: `import { runTool } from "../api/toolRunner";`
  - [ ] Add/keep: `import { apiClient } from "../api/apiClient";`

- [ ] Add state management for job status:
  ```tsx
  const [job, setJob] = React.useState<Job | null>(null);
  ```

- [ ] Render status indicators in JSX:
  ```tsx
  <JobStatusIndicator status={job?.status ?? "idle"} />
  <JobError error={error ?? job?.error ?? null} />
  ```

- [ ] Run type-check:
  ```bash
  npm run type-check -- src/components/UploadPanel.tsx
  ```

- [ ] Update corresponding test file:
  ```bash
  code web-ui/src/components/__tests__/UploadPanel.test.tsx
  ```

  - [ ] Mock `apiClient.analyzeImage` to return `{ job_id: "test-123" }`
  - [ ] Mock `apiClient.pollJob` to return full job object
  - [ ] Update test assertions

- [ ] Run tests:
  ```bash
  npm run test -- --run src/components/__tests__/UploadPanel.test.tsx
  # Should pass
  ```

### 4.2 Update `ResultsPanel.tsx`

- [ ] Open file:
  ```bash
  code web-ui/src/components/ResultsPanel.tsx
  ```

- [ ] Remove `detectToolType` import and logic:
  ```tsx
  // DELETE:
  import { detectToolType } from "../utils/detectToolType";
  const toolType = detectToolType(job.plugin_id);
  ```

- [ ] Replace conditional rendering with generic:
  ```tsx
  // DELETE:
  {toolType === "ocr" && <OcrResults result={job.result} />}
  {toolType === "yolo" && <YoloResults result={job.result} />}

  // ADD:
  <GenericJobResults result={job.result} />
  // OR:
  <pre>{JSON.stringify(job.result, null, 2)}</pre>
  // OR:
  <JobResultCard result={job.result} />
  ```

- [ ] (Per approval) Create generic result component or use JSON

- [ ] Run type-check:
  ```bash
  npm run type-check -- src/components/ResultsPanel.tsx
  ```

- [ ] Update test file:
  ```bash
  code web-ui/src/components/__tests__/ResultsPanel.test.tsx
  ```

  - [ ] Remove `detectToolType` references
  - [ ] Update assertions to match generic rendering

- [ ] Run tests:
  ```bash
  npm run test -- --run src/components/__tests__/ResultsPanel.test.tsx
  # Should pass
  ```

### 4.3 Update `VideoTracker.tsx` (if exists)

- [ ] Check if file exists:
  ```bash
  ls -la web-ui/src/components/VideoTracker.tsx
  ```

- [ ] If it exists, open it:
  ```bash
  code web-ui/src/components/VideoTracker.tsx
  ```

- [ ] Replace direct tool calls with job pipeline:
  - [ ] Find: `await runTool(pluginId, { frame })`
  - [ ] Replace with:
    ```tsx
    const { job_id } = await apiClient.analyzeImage(frameAsBlob, pluginId);
    const job = await apiClient.pollJob(job_id);
    ```

- [ ] Use full implementation from `WEB-UI_ISSUE_146.md` section "2. Updated VideoTracker"

- [ ] Add JobStatusIndicator and JobError:
  ```tsx
  <JobStatusIndicator status={job?.status ?? "idle"} />
  <JobError error={error ?? job?.error ?? null} />
  ```

- [ ] Run type-check:
  ```bash
  npm run type-check -- src/components/VideoTracker.tsx
  ```

- [ ] Update test file if exists:
  ```bash
  code web-ui/src/components/__tests__/VideoTracker.test.tsx
  ```

  - [ ] Mock `apiClient.analyzeImage`
  - [ ] Mock `apiClient.pollJob`
  - [ ] Update assertions

- [ ] Run tests:
  ```bash
  npm run test -- --run src/components/__tests__/VideoTracker.test.tsx
  ```

### 4.4 Update `AnalyzePage.tsx` (if using ToolSelector)

- [ ] Check if it imports ToolSelector:
  ```bash
  grep -n "ToolSelector" web-ui/src/pages/AnalyzePage.tsx
  ```

- [ ] If yes, replace with plugin selection dropdown:
  ```tsx
  // DELETE:
  <ToolSelector selectedPluginId={selectedPluginId} onSelectPlugin={setSelectedPluginId} />

  // ADD (option A - simple dropdown):
  const [plugins, setPlugins] = React.useState<Plugin[]>([]);
  React.useEffect(() => {
    apiClient.listPlugins().then(setPlugins);
  }, []);

  <select value={selectedPluginId || ""} onChange={(e) => setSelectedPluginId(e.target.value)}>
    <option value="">Select a plugin</option>
    {plugins.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
  </select>
  ```

- [ ] Run type-check:
  ```bash
  npm run type-check -- src/pages/AnalyzePage.tsx
  ```

---

## Phase 5: Verification (15 min)

### 5.1 No Broken Imports

- [ ] Search for deleted files/functions:
  ```bash
  cd web-ui
  rg "from.*ToolSelector" src/
  # Should return: 0 results
  rg "from.*detectToolType" src/
  # Should return: 0 results
  rg "runTool\(" src/
  # Should return: 0 results
  ```

### 5.2 Type Safety

- [ ] Run full type-check:
  ```bash
  npm run type-check
  # Should show: 0 errors
  ```

- [ ] Document any TypeScript errors:
  ```
  Error 1: _______
  Error 2: _______
  ```

- [ ] Fix each error

### 5.3 Linting

- [ ] Run full lint:
  ```bash
  npm run lint
  # Should show: 0 errors
  ```

- [ ] Document any lint errors:
  ```
  Error 1: _______
  Error 2: _______
  ```

- [ ] Fix each error

### 5.4 Testing

- [ ] Run all tests:
  ```bash
  npm run test -- --run
  # Should show: All tests passing
  ```

- [ ] Document test results:
  ```
  Total Tests: ____
  Passed: ____
  Failed: ____
  Skipped: ____
  ```

- [ ] If tests fail, debug:
  - [ ] Check mock setup (apiClient)
  - [ ] Check assertion expectations
  - [ ] Update to match new job pipeline flow

### 5.5 Manual Testing (Optional)

- [ ] Start dev server:
  ```bash
  npm run dev
  ```

- [ ] Test upload flow:
  - [ ] Select plugin
  - [ ] Upload image
  - [ ] See job status change: queued → running → done
  - [ ] See results display
  - [ ] Test error case (if possible)

- [ ] Test video tracker (if exists):
  - [ ] Start video upload
  - [ ] See frame processing with job status
  - [ ] See results overlay (if implemented)

---

## Phase 6: Commit & Push (5 min)

### 6.1 Stage Changes

- [ ] Review changes:
  ```bash
  git status
  # Should show all changes (deletions + additions + modifications)
  ```

- [ ] Review actual diffs:
  ```bash
  git diff --stat
  # Should show file counts
  ```

- [ ] Stage everything:
  ```bash
  git add -A
  ```

### 6.2 Verify Hook Requirements

- [ ] Pre-commit hooks will run:
  ```bash
  # They will check:
  # - black (formatting)
  # - ruff (linting)
  # - mypy (type checking)
  # - prevent-test-changes-without-justification
  ```

- [ ] If hook fails on test changes, include `TEST-CHANGE:` in commit message

### 6.3 Commit

- [ ] Write commit message:
  ```bash
  git commit -m "refactor(web-ui): Remove tool runner and complete job pipeline migration

  BREAKING: Old execution paths (runTool, ToolSelector, detectToolType) removed.
  All execution now goes through /v1/analyze endpoint with job polling.

  Changes:
  - Delete ToolSelector component (plugin selection via API now)
  - Delete detectToolType utility (job results are uniform)
  - Delete toolRunner.ts (use apiClient.analyzeImage + pollJob)
  - Add JobStatusIndicator component (show queued/running/done/error)
  - Add JobError component (display error messages)
  - Update UploadPanel to use job pipeline
  - Update ResultsPanel to remove tool-type branching
  - Update VideoTracker to use job pipeline

  All tests passing, type-check clean, lint clean.

  Closes #146"
  ```

### 6.4 Push

- [ ] Push to feature branch:
  ```bash
  git push -u origin refactor/web-ui-job-pipeline-cleanup
  ```

- [ ] Verify push succeeded:
  ```bash
  git log --oneline origin/refactor/web-ui-job-pipeline-cleanup
  # Should show your commit
  ```

---

## Phase 7: Pull Request (3 min)

### 7.1 Create PR

- [ ] Create PR using GitHub CLI:
  ```bash
  gh pr create \
    --title "refactor(web-ui): Remove tool runner and complete job pipeline migration" \
    --body "## Summary

Complete Web-UI migration to the job pipeline architecture by removing obsolete execution system components.

## Changes

- Delete \`ToolSelector\` component (obsolete)
- Delete \`detectToolType\` utility (no longer needed)
- Delete \`toolRunner.ts\` (replaced by apiClient)
- Add \`JobStatusIndicator\` component
- Add \`JobError\` component
- Update \`UploadPanel\` to use job pipeline
- Update \`ResultsPanel\` to remove branching
- Update \`VideoTracker\` to use job pipeline

## Verification

- All tests passing: ✅
- Type-check clean: ✅
- Lint clean: ✅
- No old imports: ✅

Closes #146"
  ```

### 7.2 Link to Issue

- [ ] PR should automatically link to issue #146

- [ ] Verify link in GitHub UI

---

## Success Criteria (Final Checklist)

- [ ] All deletions complete (3 files)
- [ ] All new components created (2 files)
- [ ] All existing components updated (3-4 files)
- [ ] All imports fixed
- [ ] All tests passing
- [ ] Type-check clean
- [ ] Lint clean
- [ ] Commit created and pushed
- [ ] PR created and linked to #146
- [ ] Branch: `refactor/web-ui-job-pipeline-cleanup`

---

## Troubleshooting

### Tests Failing

**Problem**: `apiClient.analyzeImage is not a function`  
**Solution**: Check mock in test file:
```tsx
vi.mock("../api/apiClient", () => ({
  apiClient: {
    analyzeImage: vi.fn().mockResolvedValue({ job_id: "123" }),
    pollJob: vi.fn().mockResolvedValue({ status: "done", result: {} }),
  },
}));
```

### Type Errors

**Problem**: `Cannot find module 'JobStatusIndicator'`  
**Solution**: Verify file path:
```bash
ls web-ui/src/components/JobStatusIndicator.tsx
# Should exist
```

**Problem**: `job.status is of type unknown`  
**Solution**: Define Job interface:
```tsx
interface Job {
  id: string;
  status: "queued" | "running" | "done" | "error";
  result: any;
  error?: string;
}
```

### Lint/Format Errors

**Problem**: `Unused variable 'runTool'`  
**Solution**: Remove the import line entirely

**Problem**: Pre-commit hook fails  
**Solution**: Let Black/Ruff auto-fix, then re-commit:
```bash
npm run lint  # or run the formatter
git add -A
git commit -m "refactor: ..."
```

---

## Sign-Off

**Implemented by**: ________________  
**Date**: ________________  
**Reviewed by**: ________________  
**Date**: ________________  
**Merged to main**: [ ] Yes  [ ] No  
**Date**: ________________

---

