# COMMIT 6: UI Tool Selector (Multi-Tool Support) - TODO

## Objective
Update App.tsx to use `selectedTools: string[]` instead of `selectedTool: string`, enabling multi-tool pipeline selection for VideoTracker.

## Information Gathered

### Current State Analysis:
1. **App.tsx**: Currently uses `selectedTool: string` and passes `tools={[selectedTool]}` to VideoTracker
2. **useVideoProcessor.ts**: Already updated to accept `tools: string[]` (Commit 4 - DONE)
3. **VideoTracker.tsx**: Already accepts `tools: string[]` prop (Commit 5 - DONE)
4. **App.tdd.test.tsx**: Tests still use the old `selectedTool` pattern - NEEDS UPDATE

### Files to Modify:
1. `web-ui/src/App.tsx` - Change single tool → multi-tool array
2. `web-ui/src/App.tdd.test.tsx` - Update tests for multi-tool support

---

## Plan

### Step 1: Run Pre-Commit Checks (Verify Green)
- [ ] Run server tests: `cd server && uv run pytest -q`
- [ ] Run web-ui tests: `cd web-ui && npm install && npm test`

### Step 2: Write Test First (Must FAIL)
- [ ] Update `App.tdd.test.tsx` to use `selectedTools: string[]`
- [ ] Update mock for ToolSelector to handle multi-tool
- [ ] Update tests to verify:
  - Initial state: `selectedTools` is empty array `[]`
  - Add tool: Click tool → `selectedTools` contains that tool
  - VideoTracker receives array: `tools={selectedTools}`
  - WS payload contains `tools[]`

### Step 3: Implement Code Changes
- [ ] Change `selectedTool: string` → `selectedTools: string[]` in App.tsx
- [ ] Update `handleToolChange` to add/remove tools from array
- [ ] Update `useEffect` hooks:
  - Reset `selectedTools` when plugin changes
  - Auto-select first tool when `selectedTools` is empty
- [ ] Update `handleFrame`: `{ tool: selectedTool }` → `{ tools: selectedTools }`
- [ ] Update `handleFileUpload`: use `selectedTools`
- [ ] Update VideoTracker call: `tools={[selectedTool]}` → `tools={selectedTools}`

### Step 4: Run Tests (Must PASS)
- [ ] Run web-ui tests: `cd web-ui && npm test`

### Step 5: Pre-Commit Checks Pass
- [ ] Black lint pass: `cd server && black --check .`
- [ ] Ruff lint pass: `cd server && ruff check .`
- [ ] MyPy typecheck pass: `cd server && mypy .`
- [ ] ESLint pass: `cd web-ui && npx eslint src --ext ts,tsx --max-warnings=0`

### Step 6: Commit
- [ ] Commit with message: "feat(ui): Add multi-tool selection support (Commit 6)"

---

## Code Changes Summary

### App.tsx Before:
```tsx
const [selectedTool, setSelectedTool] = useState<string>("");

// In handleFrame:
sendFrame(imageData, undefined, { tool: selectedTool });

// In VideoTracker:
<VideoTracker pluginId={selectedPlugin} tools={[selectedTool]} />
```

### App.tsx After:
```tsx
const [selectedTools, setSelectedTools] = useState<string[]>([]);

// In handleFrame:
sendFrame(imageData, undefined, { tools: selectedTools });

// In VideoTracker:
<VideoTracker pluginId={selectedPlugin} tools={selectedTools} />
```

---

## Test Cases to Add/Update

1. **Initial State Test**: `selectedTools` is empty array `[]`
2. **Add Tool Test**: Click tool → `selectedTools` contains that tool
3. **VideoTracker Receives Array**: VideoTracker receives `tools={selectedTools}` with multiple tools
4. **WS Payload Contains tools[]**: `sendFrame` payload includes `tools: selectedTools`

---

## Progress: 0/6 Steps Complete
- [ ] Step 1: Run pre-commit checks (green)
- [ ] Step 2: Write test (must fail)
- [ ] Step 3: Implement code
- [ ] Step 4: Run tests (pass)
- [ ] Step 5: Pre-commit checks pass
- [ ] Step 6: Commit

