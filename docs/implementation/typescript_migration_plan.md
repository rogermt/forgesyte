# ForgeSyte TypeScript Migration Plan

## Overview

This document outlines the complete plan for migrating the TypeScript web UI from Vision-MCP to ForgeSyte, including extraction from code2.md, branding updates, and integration with the transformed backend.

**Status**: Ready for implementation
**Priority**: High - Blocks complete UI functionality
**Estimated Effort**: 2-3 weeks (16 days)
**Target Completion**: Week 3 of ForgeSyte transformation

**Key Principle**: All work broken into small, independent units (1-2 hour tasks) to respect limited context. Each unit can be completed in a single session.

---

## Work Units Overview

This plan is divided into **22 independent work units** organized by domain. Each unit:
- Takes 1-2 hours to complete
- Can be done independently (with dependencies noted)
- Has clear acceptance criteria
- Includes verification steps
- Results in a single atomic commit

**Unit Categories**:
1. **WU-01 to WU-03**: Extraction from code2.md
2. **WU-04 to WU-07**: Project setup and configuration
3. **WU-08 to WU-10**: Branding and styling
4. **WU-11 to WU-13**: API client and WebSocket
5. **WU-14 to WU-17**: Component updates
6. **WU-18 to WU-19**: Testing framework
7. **WU-20 to WU-22**: Documentation and deployment

---

## Work Unit 1: Extract package.json from code2.md

**Objective**: Extract web-ui/package.json with ForgeSyte branding

**Duration**: 30 minutes
**Dependencies**: None

**Tasks**:
- [ ] Read code2.md lines 150-174 (package.json content)
- [ ] Create web-ui/package.json file
- [ ] Update name to "forgesyte-ui"
- [ ] Update description to ForgeSyte branding
- [ ] Add scripts: build, dev, preview, lint, type-check
- [ ] Verify JSON syntax is valid

**Verification**:
```bash
cd web-ui
npm install  # Should complete without errors
npm --version  # Should be 9+
```

**Acceptance Criteria**:
- [ ] web-ui/package.json exists with correct format
- [ ] All required scripts present
- [ ] npm install succeeds

**Related Commits**: Commit 1, Commit 2

---

## Work Unit 2: Extract TypeScript configuration files

**Objective**: Extract tsconfig.json, tsconfig.node.json from code2.md

**Duration**: 30 minutes
**Dependencies**: WU-01

**Tasks**:
- [ ] Read code2.md lines 177-200 (tsconfig.json)
- [ ] Read code2.md lines 202-214 (tsconfig.node.json)
- [ ] Create web-ui/tsconfig.json
- [ ] Create web-ui/tsconfig.node.json
- [ ] Verify JSON syntax

**Verification**:
```bash
cd web-ui
npx tsc --version  # Should work after npm install
```

**Acceptance Criteria**:
- [ ] Both tsconfig files created with valid JSON
- [ ] Strict mode enabled in tsconfig.json
- [ ] noUnusedLocals and noUnusedParameters are true

**Related Commits**: Commit 3

---

## Work Unit 3: Extract Vite configuration and HTML

**Objective**: Extract vite.config.ts and index.html from code2.md

**Duration**: 45 minutes
**Dependencies**: WU-01, WU-02

**Tasks**:
- [ ] Read code2.md lines 216-238 (vite.config.ts)
- [ ] Read code2.md lines 240-1000+ (index.html and styles)
- [ ] Create web-ui/vite.config.ts
- [ ] Create web-ui/index.html
- [ ] Create web-ui/public/ directory
- [ ] Verify HTML syntax

**Verification**:
```bash
cd web-ui
npm run build  # Should complete
tsc --noEmit   # Should have no errors
```

**Acceptance Criteria**:
- [ ] vite.config.ts created with React plugin
- [ ] index.html valid and references correct bundles
- [ ] TypeScript compilation succeeds

**Related Commits**: Commit 1, Commit 4

---

## Work Unit 4: Extract React components

**Objective**: Extract all React component .tsx files from code2.md

**Duration**: 1 hour
**Dependencies**: WU-01, WU-02, WU-03

**Tasks**:
- [ ] Locate App.tsx in code2.md and extract
- [ ] Locate CameraPreview.tsx in code2.md and extract
- [ ] Locate JobList.tsx in code2.md and extract
- [ ] Locate PluginSelector.tsx in code2.md and extract
- [ ] Locate ResultsPanel.tsx in code2.md and extract
- [ ] Create web-ui/src/components/ directory
- [ ] Place each component in correct location
- [ ] Update imports in App.tsx to use new paths

**File Structure**:
```
web-ui/src/
├── App.tsx
└── components/
    ├── CameraPreview.tsx
    ├── JobList.tsx
    ├── PluginSelector.tsx
    └── ResultsPanel.tsx
```

**Verification**:
```bash
cd web-ui
npm run type-check  # No type errors
grep -r "from './components" src/  # Should find imports
```

**Acceptance Criteria**:
- [ ] All 5 component files created
- [ ] Components have valid TypeScript syntax
- [ ] App.tsx imports components correctly
- [ ] No import path errors

**Related Commits**: Commit 1, Commit 8, Commit 9

---

## Work Unit 5: Extract hooks and API client

**Objective**: Extract useWebSocket.ts and api/client.ts from code2.md

**Duration**: 1 hour
**Dependencies**: WU-01, WU-02

**Tasks**:
- [ ] Locate useWebSocket.ts in code2.md and extract
- [ ] Locate api/client.ts in code2.md and extract
- [ ] Create web-ui/src/hooks/ directory with useWebSocket.ts
- [ ] Create web-ui/src/api/ directory with client.ts
- [ ] Update import paths in client.ts
- [ ] Verify hook and client have valid TypeScript

**File Structure**:
```
web-ui/src/
├── hooks/
│   └── useWebSocket.ts
└── api/
    └── client.ts
```

**Verification**:
```bash
cd web-ui
npm run type-check  # Should pass
grep -r "export.*useWebSocket\|export.*APIClient" src/
```

**Acceptance Criteria**:
- [ ] useWebSocket.ts exports hook function
- [ ] api/client.ts exports API client class
- [ ] Both files have valid TypeScript
- [ ] No import/export errors

**Related Commits**: Commit 1, Commit 6, Commit 7

---

## Work Unit 6: Create .gitignore and environment files

**Objective**: Create .gitignore, .env.example, and .nvmrc

**Duration**: 20 minutes
**Dependencies**: WU-01

**Tasks**:
- [ ] Create web-ui/.gitignore with Node ignores
- [ ] Create web-ui/.env.example with required variables
- [ ] Create web-ui/.nvmrc with Node version
- [ ] Add to git tracking (except .env.local)

**Files to Create**:
- `.gitignore`: node_modules, dist, .env.local, .DS_Store, etc.
- `.env.example`: VITE_API_URL, VITE_WS_URL
- `.nvmrc`: 18

**Verification**:
```bash
cd web-ui
cat .gitignore  # Should exclude node_modules, dist
cat .env.example  # Should have VITE_* variables
cat .nvmrc  # Should contain "18"
```

**Acceptance Criteria**:
- [ ] .gitignore present with Node patterns
- [ ] .env.example documents required variables
- [ ] .nvmrc specifies Node 18

**Related Commits**: Commit 1, Commit 2

---

## Work Unit 7: Create src/main.tsx and src/index.css

**Objective**: Extract main entry point and global styles

**Duration**: 30 minutes
**Dependencies**: WU-04

**Tasks**:
- [ ] Find main.tsx in code2.md
- [ ] Find index.css in code2.md
- [ ] Create web-ui/src/main.tsx
- [ ] Create web-ui/src/index.css
- [ ] Extract global styles with color palette
- [ ] Verify CSS syntax

**Verification**:
```bash
cd web-ui
npm run build  # Should include CSS in bundle
grep -i "charcoal\|forge" src/index.css  # Should have colors
```

**Acceptance Criteria**:
- [ ] main.tsx creates React root and renders App
- [ ] index.css has color variables defined
- [ ] Build includes CSS without errors

**Related Commits**: Commit 1, Commit 5

---

## Work Unit 8: Add path aliases to tsconfig.json

**Objective**: Update tsconfig.json with @/* path aliases

**Duration**: 20 minutes
**Dependencies**: WU-02

**Tasks**:
- [ ] Update tsconfig.json with baseUrl: "."
- [ ] Add paths aliases: @/*, @components/*, @hooks/*, @api/*
- [ ] Update tsconfig.node.json if needed
- [ ] Verify paths resolve correctly

**Changes**:
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@components/*": ["src/components/*"],
      "@hooks/*": ["src/hooks/*"],
      "@api/*": ["src/api/*"]
    }
  }
}
```

**Verification**:
```bash
cd web-ui
npm run type-check  # Should resolve @/ paths
```

**Acceptance Criteria**:
- [ ] Path aliases configured in tsconfig.json
- [ ] Type checker resolves @/* imports
- [ ] No path resolution errors

**Related Commits**: Commit 3

---

## Work Unit 9: Update vite.config.ts with path aliases

**Objective**: Configure Vite to use path aliases matching tsconfig

**Duration**: 20 minutes
**Dependencies**: WU-03, WU-08

**Tasks**:
- [ ] Update vite.config.ts with resolve.alias
- [ ] Add @/ and other aliases
- [ ] Add environment variable support (VITE_API_URL, VITE_WS_URL)
- [ ] Test path resolution in build

**Changes to Add**:
```typescript
import path from 'path';

resolve: {
  alias: {
    '@': path.resolve(__dirname, './src'),
  },
}
```

**Verification**:
```bash
cd web-ui
npm run build  # Should build with path aliases
npm run preview  # Should preview without errors
```

**Acceptance Criteria**:
- [ ] Vite config has resolve.alias for @/
- [ ] Environment variables supported
- [ ] Build and preview work with aliases

**Related Commits**: Commit 4

---

## Work Unit 10: Create ForgeSyte color palette in index.css

**Objective**: Define and verify ForgeSyte color system

**Duration**: 30 minutes
**Dependencies**: WU-07

**Tasks**:
- [ ] Add CSS custom properties for colors:
  - `--color-charcoal: #111318`
  - `--color-steel: #2B3038`
  - `--color-forge-orange: #FF6A00`
  - `--color-electric-cyan: #00E5FF`
- [ ] Add spacing variables (xs, sm, md, lg, xl)
- [ ] Add typography variables
- [ ] Verify color contrast ratios (WCAG AA)
- [ ] Add button, input, select styling

**Verification**:
```bash
cd web-ui
npm run build  # CSS compiles
# Check visually in dev server
npm run dev  # http://localhost:3000
```

**Acceptance Criteria**:
- [ ] All color variables defined
- [ ] Contrast ratios meet WCAG AA
- [ ] Form elements styled with palette
- [ ] CSS has no syntax errors

**Related Commits**: Commit 5

---

## Work Unit 11: Update API client.ts endpoints

**Objective**: Update API client to target ForgeSyte backend endpoints

**Duration**: 1 hour
**Dependencies**: WU-05

**Tasks**:
- [ ] Update API_BASE_URL to use VITE_API_URL env var
- [ ] Update WS_BASE_URL to use VITE_WS_URL env var
- [ ] Update all endpoint paths from /vision to /v1
- [ ] Add type definitions: PluginMetadata, JobResponse, AnalysisRequest
- [ ] Update method signatures and responses
- [ ] Add JSDoc comments to methods

**Endpoints to Update**:
- POST `/v1/analyze` (instead of `/vision/analyze`)
- GET `/v1/plugins` (instead of `/vision/plugins`)
- GET `/v1/jobs/{jobId}` (instead of `/vision/jobs/{jobId}`)
- DELETE `/v1/jobs/{jobId}` (instead of `/vision/jobs/{jobId}`)
- WebSocket `/v1/stream` (instead of `/vision/stream`)

**Verification**:
```bash
cd web-ui
npm run type-check  # No type errors
npm run build       # Compiles successfully
grep "/v1/" src/api/client.ts  # All endpoints updated
```

**Acceptance Criteria**:
- [ ] All endpoints use /v1/ path
- [ ] Type definitions added
- [ ] Environment variables used for URLs
- [ ] No Vision-MCP references remain

**Related Commits**: Commit 6

---

## Work Unit 12: Update useWebSocket hook

**Objective**: Ensure WebSocket hook matches ForgeSyte message format

**Duration**: 45 minutes
**Dependencies**: WU-05

**Tasks**:
- [ ] Add WebSocketMessage interface with ForgeSyte types
- [ ] Verify reconnection logic with exponential backoff
- [ ] Add connection status state variables
- [ ] Add proper cleanup on unmount
- [ ] Add error handling and logging
- [ ] Add JSDoc documentation

**Message Types**:
```typescript
interface WebSocketMessage {
  type: 'frame' | 'result' | 'error' | 'status';
  data?: unknown;
  error?: string;
  frame_id?: string;
}
```

**Verification**:
```bash
cd web-ui
npm run type-check  # WebSocketMessage type verified
npm run build       # Hook compiles
grep -n "reconnect\|maxRetries\|exponential" src/hooks/useWebSocket.ts
```

**Acceptance Criteria**:
- [ ] WebSocketMessage interface defined
- [ ] Reconnection logic implements exponential backoff
- [ ] Connection state properly tracked
- [ ] Cleanup happens on unmount

**Related Commits**: Commit 7

---

## Work Unit 13: Update App.tsx branding

**Objective**: Replace Vision-MCP branding with ForgeSyte in main App component

**Duration**: 30 minutes
**Dependencies**: WU-04

**Tasks**:
- [ ] Update page title from "Vision MCP" to "ForgeSyte"
- [ ] Update main heading/logo text
- [ ] Remove Vision-MCP color references
- [ ] Apply ForgeSyte color palette variables
- [ ] Update component imports to use @/ paths
- [ ] Remove any Vision-specific assets

**Search/Replace**:
- "Vision MCP Server" → "ForgeSyte"
- "vision" → "forgesyte" (where applicable)
- Direct colors → CSS variables

**Verification**:
```bash
cd web-ui
npm run type-check  # No errors
npm run build       # Builds successfully
npm run dev         # Visually inspect at localhost:3000
grep -i "vision" src/App.tsx  # Should return nothing
```

**Acceptance Criteria**:
- [ ] No "Vision" references in App.tsx
- [ ] Uses ForgeSyte color variables
- [ ] Imports use @/ path aliases
- [ ] App renders without errors

**Related Commits**: Commit 8

---

## Work Unit 14: Update CameraPreview.tsx styling

**Objective**: Apply ForgeSyte styling to CameraPreview component

**Duration**: 45 minutes
**Dependencies**: WU-04, WU-10

**Tasks**:
- [ ] Update all hardcoded colors to CSS variables
- [ ] Apply ForgeSyte color palette
- [ ] Update button styling with forge-orange
- [ ] Update error message styling
- [ ] Add loading state styling
- [ ] Verify camera functionality still works
- [ ] Add accessibility attributes

**Color Updates**:
- Buttons: Use `--color-forge-orange` instead of hardcoded
- Text: Use `--color-white` or `--color-gray`
- Backgrounds: Use `--color-charcoal` or `--color-steel`

**Verification**:
```bash
cd web-ui
npm run dev  # Test camera preview visually
npm run type-check  # No type errors
grep -i "#[0-9a-f]\{6\}" src/components/CameraPreview.tsx  # Should be minimal
```

**Acceptance Criteria**:
- [ ] Uses CSS variables instead of hardcoded colors
- [ ] ForgeSyte color palette applied
- [ ] Camera functionality works
- [ ] Accessible with keyboard and screen readers

**Related Commits**: Commit 9

---

## Work Unit 15: Update JobList.tsx with API integration

**Objective**: Connect JobList component to ForgeSyte API for job management

**Duration**: 1 hour
**Dependencies**: WU-04, WU-11

**Tasks**:
- [ ] Import apiClient from @api/client
- [ ] Add state for job list and loading
- [ ] Implement getJobStatus() call on component mount
- [ ] Add job polling with interval
- [ ] Update JobResponse type matching backend
- [ ] Add error boundary and error display
- [ ] Apply ForgeSyte styling
- [ ] Handle empty state display

**API Integration**:
```typescript
const [jobs, setJobs] = useState<JobResponse[]>([]);
const [loading, setLoading] = useState(false);

const loadJobs = async () => {
  try {
    setLoading(true);
    // Fetch jobs from API
  } catch (error) {
    // Handle error
  }
}
```

**Verification**:
```bash
cd web-ui
npm run type-check  # No type errors
npm run build       # Compiles
npm run dev         # Test with mock backend
```

**Acceptance Criteria**:
- [ ] Uses apiClient to fetch jobs
- [ ] Displays job list correctly
- [ ] Handles errors gracefully
- [ ] ForgeSyte styling applied
- [ ] Loading states work

**Related Commits**: Commit 10

---

## Work Unit 16: Update PluginSelector.tsx with plugin loading

**Objective**: Connect PluginSelector to API for plugin metadata

**Duration**: 1 hour
**Dependencies**: WU-04, WU-11

**Tasks**:
- [ ] Import apiClient and PluginMetadata type
- [ ] Add state for plugins list and loading
- [ ] Implement getPlugins() call
- [ ] Display plugin metadata (name, version, description)
- [ ] Handle plugin selection logic
- [ ] Add error handling
- [ ] Apply ForgeSyte styling
- [ ] Add loading spinner

**Plugin Display**:
```typescript
const [plugins, setPlugins] = useState<PluginMetadata[]>([]);

useEffect(() => {
  apiClient.getPlugins().then(setPlugins);
}, []);
```

**Verification**:
```bash
cd web-ui
npm run type-check  # PluginMetadata types verified
npm run build       # Compiles
npm run dev         # View plugin list
```

**Acceptance Criteria**:
- [ ] Fetches and displays plugins
- [ ] Shows plugin metadata
- [ ] Selection works
- [ ] Error handling in place
- [ ] ForgeSyte styling applied

**Related Commits**: Commit 10

---

## Work Unit 17: Update ResultsPanel.tsx with result visualization

**Objective**: Display analysis results with proper formatting and visualization

**Duration**: 1 hour
**Dependencies**: WU-04, WU-10

**Tasks**:
- [ ] Add type definitions for different result types
- [ ] Detect result type (text, image, structured)
- [ ] Add formatters for each result type
- [ ] Implement copy-to-clipboard functionality
- [ ] Add result export option
- [ ] Apply ForgeSyte styling
- [ ] Handle empty state
- [ ] Add result metadata (timestamp, plugin)

**Result Type Detection**:
```typescript
interface OCRResult {
  text: string;
  blocks: unknown[];
  confidence: number;
}

interface MotionResult {
  motion_detected: boolean;
  motion_score: number;
}
```

**Verification**:
```bash
cd web-ui
npm run type-check  # Result types verified
npm run build       # Compiles
npm run dev         # Test with different result types
```

**Acceptance Criteria**:
- [ ] Displays results for all plugin types
- [ ] Proper formatting applied
- [ ] Copy-to-clipboard works
- [ ] ForgeSyte styling consistent
- [ ] Metadata displayed

**Related Commits**: Commit 9

---

## Work Unit 18: Integrate WebSocket in CameraPreview

**Objective**: Connect CameraPreview to WebSocket for real-time streaming

**Duration**: 1 hour
**Dependencies**: WU-04, WU-12

**Tasks**:
- [ ] Import useWebSocket hook
- [ ] Get WebSocket URL from apiClient
- [ ] Implement frame capture from video element
- [ ] Send frames via WebSocket
- [ ] Receive and handle results
- [ ] Add connection status indicator
- [ ] Handle disconnection and reconnection
- [ ] Add error recovery UI

**WebSocket Integration**:
```typescript
const { isConnected, send } = useWebSocket({
  url: apiClient.getStreamUrl(selectedPlugin),
  onMessage: (msg) => {
    // Handle result
  }
});
```

**Verification**:
```bash
cd web-ui
npm run dev  # Test WebSocket with running backend
# Check browser console for WebSocket messages
```

**Acceptance Criteria**:
- [ ] WebSocket connects successfully
- [ ] Frames sent and results received
- [ ] Connection status displayed
- [ ] Reconnection works
- [ ] Error handling in place

**Related Commits**: Commit 11

---

## Work Unit 19: Setup testing framework

**Objective**: Configure Vitest and testing dependencies

**Duration**: 45 minutes
**Dependencies**: WU-01

**Tasks**:
- [ ] Add testing dependencies to package.json (vitest, react-testing-library)
- [ ] Create vitest.config.ts
- [ ] Create test setup file
- [ ] Add test script to package.json
- [ ] Create first test file structure
- [ ] Verify tests can run

**Files to Create**:
- vitest.config.ts
- src/test/setup.ts
- src/api/client.test.ts (empty)
- src/hooks/useWebSocket.test.ts (empty)

**Verification**:
```bash
cd web-ui
npm install  # Install test dependencies
npm test     # Tests run (even if empty)
```

**Acceptance Criteria**:
- [ ] Vitest configured and working
- [ ] Test script works
- [ ] Test files can be created
- [ ] Coverage reporting available

**Related Commits**: Commit 2, Commit 12

---

## Work Unit 20: Write API client unit tests

**Objective**: Add unit tests for API client methods

**Duration**: 1 hour
**Dependencies**: WU-19

**Tasks**:
- [ ] Write tests for apiClient.getPlugins()
- [ ] Write tests for apiClient.analyzeImage()
- [ ] Write tests for apiClient.getJobStatus()
- [ ] Write tests for apiClient.getStreamUrl()
- [ ] Mock fetch responses
- [ ] Test error handling paths
- [ ] Verify 80%+ coverage of client.ts

**Test Structure**:
```typescript
describe('ForgeSyteAPIClient', () => {
  it('should fetch plugins', () => {
    // Test implementation
  });
});
```

**Verification**:
```bash
cd web-ui
npm test src/api/client.test.ts  # Tests pass
npm test -- --coverage           # Check coverage
```

**Acceptance Criteria**:
- [ ] All API methods have tests
- [ ] Error cases tested
- [ ] 80%+ code coverage
- [ ] Tests pass

**Related Commits**: Commit 12

---

## Work Unit 21: Write WebSocket hook tests

**Objective**: Add unit tests for useWebSocket hook

**Duration**: 1 hour
**Dependencies**: WU-19

**Tasks**:
- [ ] Write tests for connection establishment
- [ ] Write tests for message handling
- [ ] Write tests for reconnection logic
- [ ] Write tests for cleanup on unmount
- [ ] Mock WebSocket API
- [ ] Test error scenarios
- [ ] Verify 80%+ coverage

**Test Structure**:
```typescript
describe('useWebSocket', () => {
  it('should connect to WebSocket URL', () => {
    // Test implementation
  });
});
```

**Verification**:
```bash
cd web-ui
npm test src/hooks/useWebSocket.test.ts
npm test -- --coverage
```

**Acceptance Criteria**:
- [ ] Connection lifecycle tested
- [ ] Message handling tested
- [ ] Reconnection logic tested
- [ ] 80%+ coverage
- [ ] Tests pass

**Related Commits**: Commit 12

---

## Work Unit 22: Update documentation files

**Objective**: Create web-ui documentation in CONTRIBUTING.md and docs/

**Duration**: 1 hour
**Dependencies**: WU-04, WU-19

**Tasks**:
- [ ] Update CONTRIBUTING.md with web-ui section
- [ ] Document npm commands (dev, build, test, type-check)
- [ ] Add component development patterns
- [ ] Create docs/design/web-ui-architecture.md
- [ ] Document project structure
- [ ] Document API client usage
- [ ] Document environment variables
- [ ] Add troubleshooting section

**Files to Update/Create**:
- CONTRIBUTING.md (add Web UI Development section)
- docs/design/web-ui-architecture.md (new)
- docs/design/WEB_UI_SETUP.md (new, quick start guide)

**Verification**:
```bash
# Verify documentation links
grep -r "web-ui" docs/
grep -r "npm run" CONTRIBUTING.md

# Check for broken references
find docs -name "*.md" -exec grep -l "web-ui" {} \;
```

**Acceptance Criteria**:
- [ ] CONTRIBUTING.md updated with web-ui setup
- [ ] Architecture documentation created
- [ ] All npm commands documented
- [ ] Environment variables documented
- [ ] Quick start guide available

**Related Commits**: Commit 14, Commit 15

---

## Work Unit Dependencies Graph

```
WU-01 (package.json)
  ↓
WU-02 (tsconfig) ← WU-01
WU-03 (vite, html) ← WU-01, WU-02
WU-04 (components) ← WU-01, WU-02, WU-03
WU-05 (hooks, api) ← WU-01, WU-02
WU-06 (gitignore, env) ← WU-01
WU-07 (main.tsx, css) ← WU-04
  ↓
WU-08 (path aliases) ← WU-02
WU-09 (vite aliases) ← WU-03, WU-08
WU-10 (color palette) ← WU-07
  ↓
WU-11 (API endpoints) ← WU-05
WU-12 (WebSocket hook) ← WU-05
  ↓
WU-13 (App branding) ← WU-04
WU-14 (CameraPreview styling) ← WU-04, WU-10
WU-15 (JobList API) ← WU-04, WU-11
WU-16 (PluginSelector) ← WU-04, WU-11
WU-17 (ResultsPanel) ← WU-04, WU-10
WU-18 (WebSocket integration) ← WU-04, WU-12
  ↓
WU-19 (Testing setup) ← WU-01
WU-20 (API tests) ← WU-19
WU-21 (WebSocket tests) ← WU-19
  ↓
WU-22 (Documentation) ← WU-04, WU-19
```

---

## Execution Guide

### Parallel Work Possible

These units can be done in parallel (no dependencies):
- WU-06 (while WU-02, WU-03 in progress)
- WU-19 (testing setup) can start early
- WU-20, WU-21 can run in parallel

### Recommended Sequence

**Day 1 (Extraction)**:
1. WU-01: package.json
2. WU-02: tsconfig
3. WU-03: vite config
4. WU-04: React components
5. WU-05: hooks and API

**Day 2 (Setup)**:
6. WU-06: .gitignore, env
7. WU-07: main.tsx, css
8. WU-08: Path aliases (ts)
9. WU-09: Path aliases (vite)

**Day 3 (Styling & Branding)**:
10. WU-10: Color palette
11. WU-11: API endpoints
12. WU-12: WebSocket hook
13. WU-13: App branding

**Day 4 (Components)**:
14. WU-14: CameraPreview styling
15. WU-15: JobList API
16. WU-16: PluginSelector
17. WU-17: ResultsPanel

**Day 5 (Integration & Testing)**:
18. WU-18: WebSocket integration
19. WU-19: Testing framework
20. WU-20: API tests (parallel with 21)
21. WU-21: WebSocket tests (parallel with 20)
22. WU-22: Documentation

---

## Phase 1: Extraction & Setup (Days 1-2)

### 1.1 Extract TypeScript Files from code2.md

**Objective**: Extract all TypeScript source files from `/home/rogermt/forgesyte/scratch/code2.md` and create proper project structure.

**Files to Extract**:
- `web-ui/package.json`
- `web-ui/tsconfig.json`
- `web-ui/tsconfig.node.json`
- `web-ui/vite.config.ts`
- `web-ui/index.html`
- `web-ui/src/App.tsx`
- `web-ui/src/components/CameraPreview.tsx`
- `web-ui/src/components/JobList.tsx`
- `web-ui/src/components/PluginSelector.tsx`
- `web-ui/src/components/ResultsPanel.tsx`
- `web-ui/src/hooks/useWebSocket.ts`
- `web-ui/src/api/client.ts`
- `web-ui/src/index.css`
- `web-ui/src/main.tsx`

**Output**:
```
web-ui/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css
│   ├── components/
│   │   ├── CameraPreview.tsx
│   │   ├── JobList.tsx
│   │   ├── PluginSelector.tsx
│   │   └── ResultsPanel.tsx
│   ├── hooks/
│   │   └── useWebSocket.ts
│   └── api/
│       └── client.ts
├── public/
│   └── vite.svg
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
└── .gitignore
```

**Tasks**:
- [ ] Parse code2.md and extract all TypeScript code blocks
- [ ] Create directory structure
- [ ] Write extracted files to proper locations
- [ ] Verify file structure matches project standards
- [ ] Add `.gitignore` for node_modules, dist, etc.

---

### 1.2 Setup Node Environment

**Objective**: Configure Node.js and npm for the project.

**Prerequisites**:
- Node.js 18+ installed (check: `node --version`)
- npm 9+ installed (check: `npm --version`)

**Tasks**:
- [ ] Verify Node.js/npm versions in CI/CD configuration
- [ ] Add Node.js version specification to `.nvmrc`
- [ ] Document Node.js requirements in CONTRIBUTING.md
- [ ] Update CONTRIBUTING.md with web-ui build instructions

**Commands**:
```bash
# Verify environment
node --version  # Should be >=18.0.0
npm --version   # Should be >=9.0.0

# Create .nvmrc for version consistency
echo "18" > web-ui/.nvmrc
```

---

## Phase 2: Branding & Configuration Updates (Days 3-4)

### 2.1 Update Package Configuration

**Files to Update**: `web-ui/package.json`

**Changes**:
```json
{
  "name": "forgesyte-ui",          // Changed from "vision-mcp-ui"
  "version": "0.1.0",
  "description": "ForgeSyte Web UI - Vision core for engineered systems",  // New description
  "author": "ForgeSyte Team",        // Update author
  "license": "MIT",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext ts,tsx",
    "type-check": "tsc --noEmit"     // Add type checking
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.0.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0",
    "eslint": "^8.0.0",              // Add for code quality
    "@typescript-eslint/eslint-plugin": "^6.0.0"
  }
}
```

**Tasks**:
- [ ] Update package.json with ForgeSyte branding
- [ ] Add ESLint and type-checking scripts
- [ ] Run `npm install` to create package-lock.json
- [ ] Verify all dependencies install correctly

### 2.2 Update TypeScript Configuration

**Files to Update**: `web-ui/tsconfig.json`

**Key Settings to Verify/Update**:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",                  // Add for path resolution
    "paths": {                        // Add for import shortcuts
      "@/*": ["src/*"],
      "@components/*": ["src/components/*"],
      "@hooks/*": ["src/hooks/*"],
      "@api/*": ["src/api/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**Tasks**:
- [ ] Update tsconfig.json with path aliases
- [ ] Verify strict mode is enabled
- [ ] Add JSDoc support if needed
- [ ] Test TypeScript compilation: `npm run build`

### 2.3 Update Vite Configuration

**Files to Update**: `web-ui/vite.config.ts`

**Changes Required**:
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/v1': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',  // Use env var
        changeOrigin: true,
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom'],
        },
      },
    },
  },
});
```

**Tasks**:
- [ ] Update vite.config.ts with path aliases
- [ ] Add environment variable support for API URL
- [ ] Configure output chunking for optimized builds
- [ ] Test dev server: `npm run dev`

### 2.4 Create Environment Configuration

**File to Create**: `web-ui/.env.example`

```bash
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Application
VITE_APP_NAME=ForgeSyte
VITE_APP_VERSION=0.1.0
```

**File to Create**: `web-ui/.env.local` (not committed)

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

**Tasks**:
- [ ] Create .env.example with documented variables
- [ ] Create .env.local for development (add to .gitignore)
- [ ] Document environment variables in CONTRIBUTING.md
- [ ] Add environment setup instructions to README.md

---

## Phase 3: API Integration Updates (Days 5-6)

### 3.1 Update API Client

**File**: `web-ui/src/api/client.ts`

**Changes Required**:

```typescript
/**
 * ForgeSyte API Client
 * 
 * Handles communication with ForgeSyte backend server.
 * - REST API for job management and plugin queries
 * - WebSocket for real-time streaming and results
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export interface PluginMetadata {
  name: string;
  version: string;
  description: string;
  inputs: string[];
  outputs: string[];
  config_schema?: Record<string, unknown>;
}

export interface JobResponse {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  plugin: string;
  created_at: string;
  updated_at: string;
  result?: Record<string, unknown>;
  error?: string;
}

export interface AnalysisRequest {
  plugin: string;
  image_data?: string;  // base64
  image_url?: string;
  options?: Record<string, unknown>;
}

export class ForgeSyteAPIClient {
  private baseUrl: string;
  private wsUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
    this.wsUrl = WS_BASE_URL;
  }

  /**
   * Get list of available plugins
   */
  async getPlugins(): Promise<PluginMetadata[]> {
    const response = await fetch(`${this.baseUrl}/v1/plugins`);
    if (!response.ok) throw new Error('Failed to fetch plugins');
    return response.json();
  }

  /**
   * Submit an image for analysis
   */
  async analyzeImage(request: AnalysisRequest): Promise<JobResponse> {
    const formData = new FormData();
    formData.append('plugin', request.plugin);
    
    if (request.image_url) {
      formData.append('image_url', request.image_url);
    }
    if (request.image_data) {
      formData.append('image_data', request.image_data);
    }
    if (request.options) {
      formData.append('options', JSON.stringify(request.options));
    }

    const response = await fetch(`${this.baseUrl}/v1/analyze`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) throw new Error('Analysis failed');
    return response.json();
  }

  /**
   * Get job status and results
   */
  async getJobStatus(jobId: string): Promise<JobResponse> {
    const response = await fetch(`${this.baseUrl}/v1/jobs/${jobId}`);
    if (!response.ok) throw new Error('Failed to fetch job status');
    return response.json();
  }

  /**
   * Get WebSocket URL for streaming
   */
  getStreamUrl(plugin: string, options?: Record<string, unknown>): string {
    const params = new URLSearchParams({ plugin });
    if (options) {
      params.append('options', JSON.stringify(options));
    }
    return `${this.wsUrl}/v1/stream?${params.toString()}`;
  }

  /**
   * Cancel a running job
   */
  async cancelJob(jobId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/v1/jobs/${jobId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to cancel job');
  }
}

export const apiClient = new ForgeSyteAPIClient();
```

**Key Updates**:
- [ ] Update all API endpoints to match backend
- [ ] Replace "vision" references with "forgesyte"
- [ ] Add type definitions for responses
- [ ] Support environment variables for API URLs
- [ ] Add error handling and logging
- [ ] Document all API methods with JSDoc

### 3.2 Update WebSocket Hook

**File**: `web-ui/src/hooks/useWebSocket.ts`

**Changes Required**:

```typescript
/**
 * useWebSocket Hook
 * 
 * Manages WebSocket connections for real-time streaming and results.
 * Handles reconnection, message parsing, and error recovery.
 */

import { useEffect, useCallback, useRef, useState } from 'react';

export interface WebSocketMessage {
  type: 'frame' | 'result' | 'error' | 'status';
  data?: unknown;
  error?: string;
  frame_id?: string;
}

interface UseWebSocketOptions {
  url: string;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Error) => void;
  onOpen?: () => void;
  onClose?: () => void;
  autoReconnect?: boolean;
  maxRetries?: number;
}

export function useWebSocket({
  url,
  onMessage,
  onError,
  onOpen,
  onClose,
  autoReconnect = true,
  maxRetries = 5,
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setIsConnecting(true);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        setIsConnected(true);
        setIsConnecting(false);
        reconnectAttemptsRef.current = 0;
        onOpen?.();
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage;
          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (event) => {
        const error = new Error(`WebSocket error: ${event}`);
        onError?.(error);
      };

      ws.onclose = () => {
        setIsConnected(false);
        setIsConnecting(false);
        onClose?.();

        // Attempt reconnection
        if (autoReconnect && reconnectAttemptsRef.current < maxRetries) {
          reconnectAttemptsRef.current += 1;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
          setTimeout(() => connect(), delay);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      onError?.(err);
      setIsConnecting(false);
    }
  }, [url, onMessage, onError, onOpen, onClose, autoReconnect, maxRetries]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const send = useCallback((message: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected');
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    isConnecting,
    send,
    disconnect,
  };
}
```

**Key Updates**:
- [ ] Update WebSocket URL handling to use environment variables
- [ ] Implement proper reconnection logic with exponential backoff
- [ ] Add message type safety with TypeScript
- [ ] Handle connection state properly
- [ ] Add cleanup on unmount
- [ ] Document the hook with JSDoc

---

## Phase 4: UI Component Updates (Days 7-10)

### 4.1 Update App Component

**File**: `web-ui/src/App.tsx`

**Branding Updates Required**:
- Replace "Vision MCP Server" with "ForgeSyte"
- Update color scheme to ForgeSyte palette
- Update component layout if needed
- Ensure API endpoint paths match backend

**Color Palette**:
```typescript
const colors = {
  charcoal: '#111318',      // Dark background
  steel: '#2B3038',         // Secondary background
  forgeOrange: '#FF6A00',   // Primary accent
  electricCyan: '#00E5FF',  // Secondary accent
  white: '#FFFFFF',
  gray: '#B0B8C1',
};
```

**Tasks**:
- [ ] Update page title and header
- [ ] Apply ForgeSyte color palette
- [ ] Update logo/branding if applicable
- [ ] Test styling on different screen sizes

### 4.2 Update CameraPreview Component

**File**: `web-ui/src/components/CameraPreview.tsx`

**Updates Required**:
- Verify camera access permissions
- Update styling with ForgeSyte colors
- Ensure canvas rendering works correctly
- Update error messages with ForgeSyte branding
- Add loading states with proper styling

**Tasks**:
- [ ] Test camera preview functionality
- [ ] Update error handling and messages
- [ ] Apply ForgeSyte styling
- [ ] Test on mobile devices
- [ ] Verify accessibility

### 4.3 Update JobList Component

**File**: `web-ui/src/components/JobList.tsx`

**Updates Required**:
- Update API endpoint calls to match new backend
- Update job status display to match new API response structure
- Update styling with ForgeSyte colors
- Handle new error formats
- Update timestamp formatting

**API Response Structure** (verify compatibility):
```typescript
{
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  plugin: string;
  created_at: string;      // ISO format
  updated_at: string;      // ISO format
  result?: Record<string, unknown>;
  error?: string;
}
```

**Tasks**:
- [ ] Verify job status values match backend
- [ ] Test job listing and updates
- [ ] Update error message display
- [ ] Apply ForgeSyte styling
- [ ] Test pagination if implemented

### 4.4 Update PluginSelector Component

**File**: `web-ui/src/components/PluginSelector.tsx`

**Updates Required**:
- Verify plugin metadata structure matches new backend
- Update styling with ForgeSyte colors
- Add descriptions from plugin metadata
- Update configuration options display
- Handle plugin loading states

**Expected Plugin Metadata**:
```typescript
{
  name: string;
  version: string;
  description: string;
  inputs: string[];
  outputs: string[];
  config_schema?: Record<string, unknown>;
}
```

**Tasks**:
- [ ] Test plugin loading from backend
- [ ] Verify plugin metadata display
- [ ] Test configuration options
- [ ] Apply ForgeSyte styling
- [ ] Add loading states

### 4.5 Update ResultsPanel Component

**File**: `web-ui/src/components/ResultsPanel.tsx`

**Updates Required**:
- Update result data structure to match new format
- Add result type detection (image, text, structured data)
- Update styling with ForgeSyte colors
- Add copy-to-clipboard functionality
- Improve result visualization

**Result Structure Variations**:
```typescript
// OCR results
{
  text: string;
  blocks: Block[];
  confidence: number;
}

// Motion detection
{
  motion_detected: boolean;
  motion_score: number;
  regions: Region[];
}

// Block mapper
{
  block_map: string;
  palette: string[];
  schematic: string;
}
```

**Tasks**:
- [ ] Test result rendering for each plugin type
- [ ] Add result visualization components
- [ ] Update styling with ForgeSyte colors
- [ ] Add export/download functionality
- [ ] Test with various result formats

---

## Phase 5: Styling & Theming (Days 11-12)

### 5.1 Update Global Styles

**File**: `web-ui/src/index.css`

**Changes Required**:
```css
/* ForgeSyte Color Palette */
:root {
  --color-charcoal: #111318;      /* Dark background */
  --color-steel: #2B3038;         /* Secondary background */
  --color-forge-orange: #FF6A00;  /* Primary accent */
  --color-electric-cyan: #00E5FF; /* Secondary accent */
  --color-white: #FFFFFF;
  --color-gray: #B0B8C1;
  --color-gray-dark: #6B7280;
  
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  
  --font-family-base: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  
  --border-radius: 8px;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
}

body {
  background-color: var(--color-charcoal);
  color: var(--color-white);
  font-family: var(--font-family-base);
  font-size: var(--font-size-base);
  line-height: 1.6;
  margin: 0;
  padding: 0;
}

#root {
  min-height: 100vh;
}

/* Apply ForgeSyte styling to buttons, inputs, etc. */
button {
  background-color: var(--color-forge-orange);
  color: var(--color-white);
  border: none;
  border-radius: var(--border-radius);
  padding: var(--spacing-sm) var(--spacing-md);
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s ease;
}

button:hover {
  background-color: #FF8C1F;  /* Darker shade of forge orange */
}

button:active {
  background-color: #E65A00;  /* Darker shade for active */
}

input, textarea, select {
  background-color: var(--color-steel);
  color: var(--color-white);
  border: 1px solid var(--color-gray-dark);
  border-radius: var(--border-radius);
  padding: var(--spacing-sm) var(--spacing-md);
  font-family: var(--font-family-base);
}

input:focus, textarea:focus, select:focus {
  outline: none;
  border-color: var(--color-electric-cyan);
  box-shadow: 0 0 0 3px rgba(0, 229, 255, 0.1);
}

/* Loading animation */
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.loading {
  animation: spin 1s linear infinite;
}
```

**Tasks**:
- [ ] Define CSS custom properties for colors
- [ ] Update all component styles to use variables
- [ ] Test dark theme on all components
- [ ] Ensure contrast ratios meet accessibility standards
- [ ] Test on different screen sizes

### 5.2 Component Styling Review

**Task List**:
- [ ] Review CameraPreview styling
- [ ] Review JobList styling
- [ ] Review PluginSelector styling
- [ ] Review ResultsPanel styling
- [ ] Ensure consistent spacing and typography
- [ ] Test hover/active states
- [ ] Verify mobile responsiveness

---

## Phase 6: Testing & Validation (Days 13-14)

### 6.1 Unit Tests

**File**: `web-ui/src/api/client.test.ts`

```typescript
// Test API client methods
// - Plugin fetching
// - Image analysis
// - Job status checking
// - WebSocket URL generation
```

**File**: `web-ui/src/hooks/useWebSocket.test.ts`

```typescript
// Test WebSocket hook
// - Connection establishment
// - Message handling
// - Reconnection logic
// - Cleanup on unmount
```

**Tasks**:
- [ ] Setup Jest/Vitest for testing
- [ ] Write API client unit tests
- [ ] Write WebSocket hook unit tests
- [ ] Write component unit tests
- [ ] Achieve 80%+ code coverage

### 6.2 Integration Tests

**Tests to Implement**:
- [ ] Backend API compatibility
- [ ] WebSocket streaming functionality
- [ ] Plugin loading and display
- [ ] Job submission and status tracking
- [ ] Image upload and analysis

**Commands**:
```bash
cd web-ui
npm run build          # Verify TypeScript compilation
npm run type-check     # Type safety check
npm run lint          # Code quality check
npm test              # Run tests
```

### 6.3 Browser Testing

**Test Matrix**:
- [ ] Chrome 120+ (latest)
- [ ] Firefox 121+ (latest)
- [ ] Safari 17+ (macOS/iOS)
- [ ] Edge 120+ (latest)

**Test Cases**:
- [ ] Plugin loading and selection
- [ ] Camera preview functionality
- [ ] Image upload and analysis
- [ ] WebSocket streaming
- [ ] Job status updates
- [ ] Error handling and recovery
- [ ] Mobile responsiveness
- [ ] Accessibility (keyboard navigation, screen readers)

### 6.4 Performance Testing

**Metrics to Monitor**:
- [ ] Page load time < 3s
- [ ] Time to interactive < 4s
- [ ] WebSocket message latency < 100ms
- [ ] Image upload handling (test 5MB+ files)
- [ ] Memory usage under sustained use

**Commands**:
```bash
cd web-ui
npm run build          # Verify production build
npm run preview        # Preview production build locally
```

---

## Phase 7: Backend Integration (Days 15)

### 7.1 API Compatibility Check

**Verify Backend Endpoints**:
- [ ] GET `/v1/plugins` - Returns array of PluginMetadata
- [ ] POST `/v1/analyze` - Accepts FormData, returns JobResponse
- [ ] GET `/v1/jobs/{job_id}` - Returns JobResponse
- [ ] DELETE `/v1/jobs/{job_id}` - Cancels job
- [ ] WebSocket `/v1/stream` - Accepts frames, returns results

**CORS Configuration**:
- [ ] Verify CORS headers allow web-ui origin
- [ ] Test both dev (localhost:3000) and production URLs
- [ ] Test CORS with OPTIONS preflight requests

### 7.2 Environment Configuration

**Development Setup**:
```bash
# Create web-ui/.env.local
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Run dev server
npm run dev
# Visit http://localhost:3000
```

**Production Setup**:
```bash
# Create web-ui/.env.production
VITE_API_URL=https://api.example.com
VITE_WS_URL=wss://api.example.com

# Build for production
npm run build
# Output in web-ui/dist/
```

**Tasks**:
- [ ] Document environment variable requirements
- [ ] Create example .env files
- [ ] Test with actual backend
- [ ] Verify API endpoint connectivity
- [ ] Test WebSocket connections

### 7.3 Documentation Updates

**Files to Update**:
- [ ] README.md - Add web-ui section
- [ ] CONTRIBUTING.md - Add web development setup
- [ ] ARCHITECTURE.md - Add web UI architecture
- [ ] docs/design/ - Add web UI design document

**Content to Add**:
- Web development setup instructions
- Running dev server
- Building for production
- Environment configuration
- Component architecture
- API integration guide

**Tasks**:
- [ ] Update CONTRIBUTING.md with web-ui instructions
- [ ] Add web UI section to README.md
- [ ] Document component structure
- [ ] Document API integration patterns
- [ ] Add troubleshooting guide

---

## Phase 8: Deployment & CI/CD (Days 16)

### 8.1 Build Optimization

**Vite Configuration**:
- [ ] Code splitting for React + libraries
- [ ] Asset minification
- [ ] Source maps for production debugging
- [ ] Environment-specific builds

**Build Commands**:
```bash
# Development build
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

### 8.2 Docker Integration

**File**: `web-ui/Dockerfile` (new)

```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Serve stage
FROM node:18-alpine
WORKDIR /app

RUN npm install -g serve

COPY --from=builder /app/dist ./dist

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
```

**File**: `web-ui/.dockerignore` (new)

```
node_modules
npm-debug.log
dist
.env.local
.git
```

**Tasks**:
- [ ] Create Dockerfile for web-ui
- [ ] Test Docker build locally
- [ ] Add Docker build to CI/CD pipeline
- [ ] Document Docker deployment

### 8.3 CI/CD Pipeline Integration

**GitHub Actions**: `.github/workflows/web-ui-ci.yml`

```yaml
name: Web UI CI/CD

on:
  push:
    branches: [main, develop]
    paths:
      - 'web-ui/**'
      - '.github/workflows/web-ui-ci.yml'
  pull_request:
    branches: [main, develop]
    paths:
      - 'web-ui/**'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd web-ui && npm ci
      - run: cd web-ui && npm run type-check
      - run: cd web-ui && npm run lint
      - run: cd web-ui && npm run build
      - run: cd web-ui && npm test

  build-docker:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: test
    steps:
      - uses: actions/checkout@v3
      - uses: docker/setup-buildx-action@v2
      - uses: docker/build-push-action@v4
        with:
          context: ./web-ui
          push: false
          tags: forgesyte-ui:${{ github.sha }}
```

**Tasks**:
- [ ] Create GitHub Actions workflow
- [ ] Test CI/CD pipeline
- [ ] Set up Docker image registry
- [ ] Configure deployment triggers

---

## Success Criteria

### ✅ Completion Checklist

#### Extraction & Setup
- [ ] All TypeScript files extracted from code2.md
- [ ] Project structure created correctly
- [ ] Node.js/npm environment configured
- [ ] Dependencies install successfully

#### Branding & Configuration
- [ ] ForgeSyte branding applied throughout
- [ ] Color palette implemented consistently
- [ ] Environment variables configured
- [ ] Build configuration updated

#### API Integration
- [ ] API client updated with new endpoints
- [ ] WebSocket integration functional
- [ ] Error handling implemented
- [ ] Type definitions complete

#### Components
- [ ] All components updated with ForgeSyte styling
- [ ] API integration tested in each component
- [ ] Mobile responsiveness verified
- [ ] Accessibility requirements met

#### Testing
- [ ] Unit tests written and passing
- [ ] Integration tests with backend passing
- [ ] Cross-browser testing completed
- [ ] Performance targets met
- [ ] 80%+ code coverage achieved

#### Documentation
- [ ] CONTRIBUTING.md updated
- [ ] README.md updated
- [ ] ARCHITECTURE.md updated
- [ ] Components documented
- [ ] API integration guide written

#### Deployment
- [ ] Production build optimized
- [ ] Docker image builds successfully
- [ ] CI/CD pipeline configured
- [ ] Environment-specific configs working

---

## Risk Mitigation

### Potential Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| API incompatibility | High | Regular testing against actual backend; version compatibility matrix |
| WebSocket issues | High | Comprehensive testing; fallback to polling if needed |
| Performance degradation | Medium | Profiling during development; lazy loading components |
| Cross-browser issues | Medium | Testing on multiple browsers early; polyfill strategy |
| Type safety gaps | Medium | Strict TypeScript config; pre-commit type checking |
| Mobile responsiveness | Medium | Mobile-first design; testing on physical devices |
| Build issues | Low | Monorepo testing; clear dependency documentation |

---

## Dependencies

### Runtime
- React 18+
- React DOM 18+

### Development
- TypeScript 5+
- Vite 5+
- Node 18+
- npm 9+

### Testing (to be added)
- Vitest or Jest
- React Testing Library
- Mock Service Worker (for API mocking)

---

## Deliverables

### Phase 1: Extraction & Setup
- ✅ web-ui directory structure
- ✅ All TypeScript files extracted
- ✅ Node environment configured
- ✅ Dependencies installed

### Phase 2: Branding & Configuration
- ✅ Updated package.json
- ✅ Updated tsconfig.json
- ✅ Updated vite.config.ts
- ✅ Environment configuration files
- ✅ Color palette CSS variables

### Phase 3: API Integration
- ✅ Updated API client (client.ts)
- ✅ Updated WebSocket hook (useWebSocket.ts)
- ✅ Type definitions
- ✅ Error handling

### Phase 4: Components
- ✅ App.tsx updated
- ✅ CameraPreview.tsx updated
- ✅ JobList.tsx updated
- ✅ PluginSelector.tsx updated
- ✅ ResultsPanel.tsx updated

### Phase 5: Styling & Theming
- ✅ Global styles updated (index.css)
- ✅ Component styles reviewed
- ✅ Responsive design verified

### Phase 6: Testing & Validation
- ✅ Unit tests
- ✅ Integration tests
- ✅ Browser testing completed
- ✅ Performance validation

### Phase 7: Backend Integration
- ✅ API compatibility verified
- ✅ WebSocket functionality tested
- ✅ Documentation updated

### Phase 8: Deployment & CI/CD
- ✅ Production build optimized
- ✅ Docker image created
- ✅ CI/CD pipeline configured
- ✅ Deployment documentation

---

## Timeline Summary

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| 1: Extraction & Setup | 2 days | Week 3, Day 1 | Week 3, Day 2 |
| 2: Branding & Configuration | 2 days | Week 3, Day 3 | Week 3, Day 4 |
| 3: API Integration | 2 days | Week 3, Day 5 | Week 3, Day 6 |
| 4: Components | 4 days | Week 3, Day 7 | Week 4, Day 3 |
| 5: Styling & Theming | 2 days | Week 4, Day 4 | Week 4, Day 5 |
| 6: Testing & Validation | 2 days | Week 4, Day 6 | Week 4, Day 7 |
| 7: Backend Integration | 1 day | Week 4, Day 8 | Week 4, Day 8 |
| 8: Deployment & CI/CD | 1 day | Week 4, Day 9 | Week 4, Day 9 |
| **Total** | **16 days** | **Week 3, Day 1** | **Week 4, Day 9** |

---

## Commit Strategy

This section details the commit workflow for implementing the TypeScript migration, following AGENTS.md conventions and atomic commit principles.

### Branch Management

**Branch Creation**:
```bash
git checkout -b feature/typescript-migration
```

**Never commit directly to main**. All changes go through feature branch → local merge → push.

### Commit Naming Convention

Follow conventional commits:
- `feat:` - New feature
- `refactor:` - Code reorganization without behavior change
- `chore:` - Configuration, dependencies, build system
- `docs:` - Documentation updates
- `test:` - Testing additions
- `fix:` - Bug fixes

### Phase 1: Extraction & Setup (2 commits)

#### Commit 1: "feat: Extract TypeScript web-ui from code2.md"
```bash
git add web-ui/src web-ui/public web-ui/*.json web-ui/*.html web-ui/*.ts
git commit -m "feat: Extract TypeScript web-ui from code2.md

- Extract all TypeScript source files from scratch/code2.md
- Create web-ui directory structure with React + TypeScript setup
- Add src/, public/, config files (tsconfig, vite, package.json)
- Create .gitignore for Node dependencies and build artifacts
- Verify initial TypeScript compilation succeeds"
```

**Test After Commit**:
```bash
cd web-ui
npm install
npm run build        # Should compile successfully
npm run type-check   # Should have no type errors
```

#### Commit 2: "chore: Update web-ui package configuration"
```bash
git add web-ui/package.json web-ui/.nvmrc web-ui/.env.example
git commit -m "chore: Update web-ui package configuration

- Update package.json with ForgeSyte branding and metadata
- Add type-check and lint scripts for code quality
- Create .nvmrc for Node.js version consistency
- Create .env.example with required environment variables
- Pin dependency versions for reproducibility"
```

**Test After Commit**:
```bash
npm install       # Verify dependencies install
npm run build     # Verify build succeeds
```

---

### Phase 2: Configuration & Branding (3 commits)

#### Commit 3: "refactor: Update TypeScript configuration for ForgeSyte"
```bash
git add web-ui/tsconfig.json web-ui/tsconfig.node.json
git commit -m "refactor: Update TypeScript configuration for ForgeSyte

- Add path aliases (@/, @components/*, @hooks/*, @api/*) for cleaner imports
- Enable strict mode for enhanced type safety
- Configure module resolution for bundler target
- Ensure noUnusedLocals and noUnusedParameters enabled
- Update jsxImportSource to react-jsx for React 17+ JSX transform"
```

**Test After Commit**:
```bash
npm run type-check   # Should pass with no errors
```

#### Commit 4: "refactor: Update Vite and build configuration"
```bash
git add web-ui/vite.config.ts web-ui/index.html
git commit -m "refactor: Update Vite and build configuration

- Add path alias resolution in Vite config
- Configure environment variable support (VITE_* prefix)
- Update API proxy to use environment variable for target
- Add output chunking for optimized production builds
- Update index.html with ForgeSyte branding and meta tags"
```

**Test After Commit**:
```bash
npm run build      # Should build successfully
npm run preview    # Should preview correctly
```

#### Commit 5: "feat: Add ForgeSyte color palette and global styles"
```bash
git add web-ui/src/index.css
git commit -m "feat: Add ForgeSyte color palette and global styles

- Define ForgeSyte CSS custom properties (charcoal, steel, forge-orange, cyan)
- Implement global styles for body, typography, spacing
- Style form elements (inputs, buttons, selects) with ForgeSyte colors
- Add loading animation and interactive states
- Ensure WCAG AA contrast ratio compliance"
```

**Test After Commit**:
```bash
npm run dev        # Visually inspect styles in dev server
```

---

### Phase 3: API Integration (2 commits)

#### Commit 6: "feat: Update API client for ForgeSyte backend"
```bash
git add web-ui/src/api/client.ts
git commit -m "feat: Update API client for ForgeSyte backend

- Replace Vision-MCP endpoints with ForgeSyte /v1/* endpoints
- Add type definitions for PluginMetadata, JobResponse, AnalysisRequest
- Implement ForgeSyteAPIClient class with methods for:
  - getPlugins(): Fetch available plugins
  - analyzeImage(): Submit image for analysis
  - getJobStatus(): Check job status
  - cancelJob(): Cancel running job
  - getStreamUrl(): Get WebSocket URL
- Support environment variables for API/WebSocket URLs
- Add comprehensive error handling and logging"
```

**Test After Commit**:
```bash
npm run type-check   # Verify types are correct
npm run build        # Verify compilation succeeds
```

#### Commit 7: "feat: Implement WebSocket hook for real-time streaming"
```bash
git add web-ui/src/hooks/useWebSocket.ts
git commit -m "feat: Implement WebSocket hook for real-time streaming

- Create useWebSocket hook for WebSocket connection management
- Implement connection, reconnection with exponential backoff
- Add message type safety with TypeScript interfaces
- Handle connection lifecycle (open, close, error, message)
- Implement max retry attempts and cleanup on unmount
- Support custom callbacks for message/error/connect events"
```

**Test After Commit**:
```bash
npm run type-check   # Verify hook types
npm run build        # Verify compilation
```

---

### Phase 4: Component Updates (4 commits)

#### Commit 8: "refactor: Update App.tsx with ForgeSyte branding"
```bash
git add web-ui/src/App.tsx
git commit -m "refactor: Update App.tsx with ForgeSyte branding

- Update page title and main heading to ForgeSyte
- Apply ForgeSyte color scheme to main layout
- Update component structure to use path aliases
- Ensure all imports use new @/* path aliases
- Remove Vision-MCP specific code and branding"
```

**Test After Commit**:
```bash
npm run dev        # Visually inspect App component
npm run type-check # Verify types
```

#### Commit 9: "refactor: Update components with ForgeSyte styling"
```bash
git add web-ui/src/components/
git commit -m "refactor: Update components with ForgeSyte styling

- Update CameraPreview with ForgeSyte colors and accessibility
- Update JobList to match new API response structure
- Update PluginSelector with plugin metadata handling
- Update ResultsPanel with result type detection and visualization
- Apply consistent spacing and typography across components
- Ensure all components use CSS custom properties for theming"
```

**Test After Commit**:
```bash
npm run dev        # Test each component visually
npm run type-check # Verify all type errors resolved
```

#### Commit 10: "feat: Add API integration to components"
```bash
git add web-ui/src/components/JobList.tsx web-ui/src/components/PluginSelector.tsx
git commit -m "feat: Add API integration to components

- Integrate ForgeSyteAPIClient into JobList component
- Integrate plugin fetching into PluginSelector
- Add loading and error states for API calls
- Handle response data structure from new backend
- Add proper error messaging and user feedback
- Implement job status polling and updates"
```

**Test After Commit**:
```bash
npm run type-check # Verify API integration types
npm run build      # Verify production build succeeds
```

#### Commit 11: "feat: Implement WebSocket integration for streaming"
```bash
git add web-ui/src/components/CameraPreview.tsx
git commit -m "feat: Implement WebSocket integration for streaming

- Integrate useWebSocket hook into CameraPreview
- Implement frame capture and transmission via WebSocket
- Handle streaming results and display updates
- Add connection status indicator and error recovery
- Ensure proper cleanup and resource management
- Test with actual backend WebSocket endpoint"
```

**Test After Commit**:
```bash
npm run dev        # Test WebSocket functionality
npm run type-check # Verify all types correct
```

---

### Phase 5: Testing & Validation (2 commits)

#### Commit 12: "test: Add unit tests for API client and hooks"
```bash
git add web-ui/src/api/client.test.ts web-ui/src/hooks/useWebSocket.test.ts web-ui/vitest.config.ts
git commit -m "test: Add unit tests for API client and hooks

- Add API client unit tests for all methods
- Add WebSocket hook tests for connection lifecycle
- Test reconnection logic and error handling
- Mock API responses and WebSocket messages
- Configure Vitest/Jest for the project
- Achieve 80%+ code coverage for critical paths"
```

**Test After Commit**:
```bash
npm test           # All tests should pass
npm test -- --coverage  # Verify coverage
```

#### Commit 13: "test: Add integration tests with backend"
```bash
git add web-ui/src/integration/ web-ui/vitest.integration.config.ts
git commit -m "test: Add integration tests with backend

- Add integration tests for API client with real endpoints
- Test WebSocket streaming functionality
- Test complete job submission and status workflow
- Test plugin loading and display
- Test error handling and recovery scenarios
- Document testing procedures for CI/CD"
```

**Test After Commit**:
```bash
npm run test:integration  # Run integration tests
```

---

### Phase 6: Documentation (2 commits)

#### Commit 14: "docs: Update CONTRIBUTING.md for web-ui development"
```bash
git add CONTRIBUTING.md
git commit -m "docs: Update CONTRIBUTING.md for web-ui development

- Add web-ui development setup instructions
- Document npm commands and workflow
- Add TypeScript and ESLint guidelines
- Document environment variable setup
- Add component development patterns
- Include testing requirements and procedures"
```

#### Commit 15: "docs: Add web-ui architecture and component docs"
```bash
git add docs/design/web-ui-architecture.md docs/design/web-ui-components.md
git commit -m "docs: Add web-ui architecture and component docs

- Document web-ui project structure and architecture
- Create component usage guide and patterns
- Document API client and WebSocket integration
- Add styling guide with color palette reference
- Document build process and deployment
- Update ARCHITECTURE.md with web-ui section"
```

**Test After Commit**:
```bash
# Verify all documentation links work
grep -r 'web-ui' docs/
```

---

### Phase 7: Deployment & CI/CD (2 commits)

#### Commit 16: "chore: Add Docker support for web-ui"
```bash
git add web-ui/Dockerfile web-ui/.dockerignore
git commit -m "chore: Add Docker support for web-ui

- Create Dockerfile for building and serving web-ui
- Configure multi-stage build (builder + serve stages)
- Add .dockerignore for efficient image building
- Test Docker image build and run locally
- Document Docker deployment process"
```

**Test After Commit**:
```bash
docker build -t forgesyte-ui:latest web-ui/
docker run -p 3000:3000 forgesyte-ui:latest
# Visit http://localhost:3000 to verify
```

#### Commit 17: "ci: Add GitHub Actions workflow for web-ui"
```bash
git add .github/workflows/web-ui-ci.yml
git commit -m "ci: Add GitHub Actions workflow for web-ui

- Create CI workflow for type checking and linting
- Add test step with coverage reporting
- Add Docker image build on main branch
- Configure deployment trigger conditions
- Document CI/CD process and requirements"
```

---

### Final Merge to Main

After all commits are complete and tested:

```bash
# Ensure all tests pass
npm run build
npm run type-check
npm test

# Verify git status is clean
git status

# Switch to main
git checkout main

# Pull latest changes
git pull origin main

# Merge feature branch
git merge feature/typescript-migration

# Push to origin
git push origin main
```

---

### Commit Checklist Template

Use this checklist before each commit:

```
BEFORE COMMITTING:
- [ ] Changes are atomic and focused
- [ ] TypeScript compilation passes (npm run build)
- [ ] Type checking passes (npm run type-check)
- [ ] Linting passes (npm run lint)
- [ ] Tests pass (npm test)
- [ ] No console errors in dev server
- [ ] Documentation updated if needed
- [ ] Commit message follows conventional commits
- [ ] Related files are staged and ready

AFTER COMMITTING:
- [ ] Run full test suite one more time
- [ ] Visually test changes in dev server
- [ ] Verify no regressions in related code
```

---

### Rollback Strategy

If a commit introduces issues:

```bash
# Identify problematic commit
git log --oneline

# Revert the commit
git revert <commit-hash>

# Fix the issue
# Make corrections...

# Create new commit with fixes
git add .
git commit -m "fix: Resolve issues from previous TypeScript migration commit"

# Continue workflow
```

---

### Key Metrics & Validation

**After Each Commit Verify**:
- [ ] TypeScript compilation succeeds
- [ ] No type errors (`npm run type-check`)
- [ ] Linting passes (`npm run lint`)
- [ ] Tests pass (`npm test`)
- [ ] Build succeeds (`npm run build`)
- [ ] No console warnings/errors in dev

**Final Validation**:
- [ ] All 17 commits complete
- [ ] Feature branch merged to main
- [ ] All tests passing
- [ ] Docker image builds successfully
- [ ] CI/CD pipeline green
- [ ] Documentation complete and accurate

---

## Getting Started

### Immediate Next Steps (Today)

1. **Create branch for TypeScript migration**:
   ```bash
   git checkout -b feature/typescript-migration
   ```

2. **Extract TypeScript files from code2.md**:
   - Parse `/home/rogermt/forgesyte/scratch/code2.md`
   - Create `/home/rogermt/forgesyte/web-ui/` directory
   - Extract all TypeScript files

3. **Initialize Node environment**:
   ```bash
   cd web-ui
   npm install
   ```

4. **Verify initial build**:
   ```bash
   npm run build
   ```

5. **Begin Phase 2 (Branding Updates)**:
   - Update package.json
   - Update configuration files
   - Apply ForgeSyte color palette

---

## Contact & Support

For questions or blockers during implementation:
- Review ARCHITECTURE.md for system design
- Check CONTRIBUTING.md for development workflow
- Consult PLUGIN_DEVELOPMENT.md for plugin integration details
- Reference vision-mcp_vs_forgesyte_comparison.md for original implementation details

---

**Document Version**: 1.0  
**Last Updated**: January 9, 2026  
**Status**: Ready for Implementation  
**Owner**: ForgeSyte Team
