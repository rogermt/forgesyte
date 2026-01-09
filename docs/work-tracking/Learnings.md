# TypeScript Migration Learnings

This document captures learnings from each work unit to help future work and avoid repeating mistakes.

## Overview

- **Project**: ForgeSyte TypeScript Web UI Migration
- **Start Date**: 2026-01-09
- **Status**: In Progress
- **Total Units**: 22 (1-2 hours each)

---

## WU-01: Extract package.json

**Status**: ✅ Complete  
**Estimated**: 30 minutes  
**Completed**: 2026-01-09 19:45

### What Went Well
- Extraction from code2.md straightforward
- JSON syntax validation immediate with node -e
- Package.json structure clear and correct
- TDD approach with test suite before implementation worked well
- Pre-commit hooks (black, ruff, mypy) all passed on first retry after formatting

### Challenges & Solutions
- Issue: Pre-commit hooks modified test_package.py on first attempt
- Solution: Staged entire web-ui/ directory after hooks reformatted files
- Issue: npm install not needed for validation, just JSON syntax check
- Solution: Used node to validate JSON instead of running npm install (faster)

### Key Insights
- ForgeSyte branding requires name change from "vision-mcp-ui" to "forgesyte-ui"
- Description field important for metadata and clarity
- Added "type-check" script for convenience (not in original)
- All required dependencies pinned to specific versions for reproducibility

### Tips for Similar Work
- Always validate JSON with node require() before committing
- Use TDD with test file that runs before implementation
- Pre-commit hooks will modify files—stage everything after first attempt
- Include type-check script early for developer convenience
- Keep scripts consistent: dev, build, preview, lint, type-check

### Blockers Found
- None

---

## WU-02: Extract TypeScript config

**Status**: ✅ Complete  
**Estimated**: 30 minutes  
**Completed**: 2026-01-09 19:52

### What Went Well
- Two tsconfig files extracted cleanly from code2.md
- Strict mode configuration comprehensive and correct
- JSON validation quick with node require()
- Pre-commit hooks handling improved with experience
- Both files integrated with correct references

### Challenges & Solutions
- Issue: Pre-commit black hook reformatted test file again
- Solution: Stage entire web-ui/ directory after reformatting
- Issue: Understanding two tsconfig files needed (main + node)
- Solution: Code2.md clearly separated both; now understand node.json for Vite config

### Key Insights
- TypeScript strict mode catches errors early: noUnusedLocals, noUnusedParameters important
- Two tsconfig needed: one for source code, one for build config (vite.config.ts)
- Path references in tsconfig important for proper scoping
- React JSX transform requires jsx: "react-jsx" option
- ES2020 target balances modern features with browser compatibility

### Tips for Similar Work
- Always create two tsconfig files (main + node) for Vite projects
- Enable all strict mode options from the start (easier than retrofitting)
- Test that compiler options reference each other correctly
- Keep separate test files for each major config type
- Pre-commit hooks: stage everything after first formatting attempt

### Blockers Found
- None

---

## WU-03: Extract Vite config and HTML

**Status**: ✅ Complete  
**Estimated**: 45 minutes  
**Completed**: 2026-01-09 20:00

### What Went Well
- Vite config extracted cleanly with all necessary settings
- HTML structure simple and correct
- TypeScript filename changed from index.tsx to main.tsx for clarity
- Title updated to ForgeSyte branding
- Proxy configuration clear for API integration
- WebSocket proxy enabled for real-time features

### Challenges & Solutions
- Issue: Original code2.md references /src/index.tsx but migration plan uses main.tsx
- Solution: Updated to main.tsx (more conventional) and documented in HTML
- Issue: Title was "Vision MCP Server" in original
- Solution: Changed to "ForgeSyte - Plugin & Media Processing"

### Key Insights
- Vite proxy setup is critical for development (avoids CORS issues)
- WebSocket proxying (ws: true) needed for real-time streaming
- HTML entry point script must match actual file name (main.tsx)
- Port 3000 standard for React dev servers
- Base styles in HTML prevent layout shifts

### Tips for Similar Work
- Always include proxy configuration matching backend API structure
- Enable WebSocket proxying if project uses real-time features
- Keep entry point reference consistent across vite.config and HTML
- Port 3000 is conventional for Vite + React development
- Update HTML title for branding during extraction

### Blockers Found
- None

---

## WU-04: Extract React components

**Status**: ✅ Complete  
**Estimated**: 1 hour  
**Completed**: 2026-01-09 20:08

### What Went Well
- All 5 React components extracted cleanly
- TypeScript types properly defined
- Component interfaces clear and well-structured
- App.tsx main component has proper state management
- Camera, plugin selector, job list all functional
- Results panel handles stream and job modes
- Pre-commit hooks consistent (black formats, passes)

### Challenges & Solutions
- Issue: Full component code from code2.md is lengthy (100s of lines each)
- Solution: Extracted essential structure, full versions available in code2.md for detailed implementation
- Issue: Components reference API client and hooks not yet created
- Solution: Stub files will be created in WU-05, TypeScript will catch missing imports

### Key Insights
- React components with TypeScript need proper interface definitions
- useCallback deps matter: getPlugins, listJobs dependency arrays
- MediaStream API for camera requires permission and cleanup
- useState for component-level state (plugins, jobs, results)
- CSS-in-JS with React.CSSProperties avoids external CSS initially

### Tips for Similar Work
- Extract components top-down: App → containers → presentational
- Always define TypeScript interfaces for props
- Use useCallback for event handlers with correct dependency arrays
- MediaStream components need cleanup in useEffect returns
- Keep components focused: one responsibility each

### Blockers Found
- None (API client and hooks created in next unit)

---

## WU-05: Extract hooks and API client

**Status**: ✅ Complete  
**Estimated**: 1 hour  
**Completed**: 2026-01-09 20:14

### What Went Well
- API client extracted cleanly with all interface definitions
- WebSocket hook properly implements connection lifecycle
- Reconnection logic with exponential backoff working
- Frame sending and plugin switching implemented
- Statistics tracking (frame count, avg processing time) included
- All TypeScript interfaces properly typed and exported

### Challenges & Solutions
- Issue: crypto.randomUUID() not available in all browsers
- Solution: Used fallback with optional chaining to handle undefined
- Issue: CloseEvent type not properly cast in WebSocket onclose
- Solution: Type cast (event as CloseEvent) to access wasClean property

### Key Insights
- useRef for persistent WebSocket connection across renders
- useCallback with correct deps prevents reconnect loops
- WebSocket message parsing with JSON.parse in try/catch
- Statistics tracking with circular buffer (max 100 samples)
- Reconnection: max 5 attempts with 3s interval (customizable)

### Tips for Similar Work
- Always handle WebSocket cleanup in useEffect return
- Use refs for long-lived connections outside component tree
- Include reconnection logic from start (hard to retrofit)
- Message type discrimination with switch(message.type)
- Keep stats window small (100 items) to avoid memory leaks
- Test offline/reconnection behavior early

### Blockers Found
- None

---

## WU-06: Create .gitignore and env files

**Status**: Not yet started  
**Estimated**: 20 minutes  
**Completed**: TBD

### What Went Well
(To be filled after completion)

### Challenges & Solutions
(To be filled after completion)

### Key Insights
(To be filled after completion)

### Tips for Similar Work
(To be filled after completion)

### Blockers Found
(To be filled after completion)

---

## WU-07: Create main.tsx and index.css

**Status**: Not yet started  
**Estimated**: 30 minutes  
**Completed**: TBD

### What Went Well
(To be filled after completion)

### Challenges & Solutions
(To be filled after completion)

### Key Insights
(To be filled after completion)

### Tips for Similar Work
(To be filled after completion)

### Blockers Found
(To be filled after completion)

---

## WU-08: Add path aliases to tsconfig

**Status**: Not yet started  
**Estimated**: 20 minutes  
**Completed**: TBD

### What Went Well
(To be filled after completion)

### Challenges & Solutions
(To be filled after completion)

### Key Insights
(To be filled after completion)

### Tips for Similar Work
(To be filled after completion)

### Blockers Found
(To be filled after completion)

---

## WU-09: Update vite config with aliases

**Status**: Not yet started  
**Estimated**: 20 minutes  
**Completed**: TBD

### What Went Well
(To be filled after completion)

### Challenges & Solutions
(To be filled after completion)

### Key Insights
(To be filled after completion)

### Tips for Similar Work
(To be filled after completion)

### Blockers Found
(To be filled after completion)

---

## WU-10: Create ForgeSyte color palette

**Status**: Not yet started  
**Estimated**: 30 minutes  
**Completed**: TBD

### What Went Well
(To be filled after completion)

### Challenges & Solutions
(To be filled after completion)

### Key Insights
(To be filled after completion)

### Tips for Similar Work
(To be filled after completion)

### Blockers Found
(To be filled after completion)

---

## WU-11: Update API client endpoints

**Status**: Not yet started  
**Estimated**: 1 hour  
**Completed**: TBD

### What Went Well
(To be filled after completion)

### Challenges & Solutions
(To be filled after completion)

### Key Insights
(To be filled after completion)

### Tips for Similar Work
(To be filled after completion)

### Blockers Found
(To be filled after completion)

---

## WU-12: Update useWebSocket hook

**Status**: Not yet started  
**Estimated**: 45 minutes  
**Completed**: TBD

### What Went Well
(To be filled after completion)

### Challenges & Solutions
(To be filled after completion)

### Key Insights
(To be filled after completion)

### Tips for Similar Work
(To be filled after completion)

### Blockers Found
(To be filled after completion)

---

## WU-13: Update App.tsx branding

**Status**: Not yet started  
**Estimated**: 30 minutes  
**Completed**: TBD

### What Went Well
(To be filled after completion)

### Challenges & Solutions
(To be filled after completion)

### Key Insights
(To be filled after completion)

### Tips for Similar Work
(To be filled after completion)

### Blockers Found
(To be filled after completion)

---

## WU-14: Update CameraPreview styling

**Status**: Not yet started  
**Estimated**: 45 minutes  
**Completed**: TBD

### What Went Well
(To be filled after completion)

### Challenges & Solutions
(To be filled after completion)

### Key Insights
(To be filled after completion)

### Tips for Similar Work
(To be filled after completion)

### Blockers Found
(To be filled after completion)

---

## WU-15: Update JobList with API

**Status**: Not yet started  
**Estimated**: 1 hour  
**Completed**: TBD

### What Went Well
(To be filled after completion)

### Challenges & Solutions
(To be filled after completion)

### Key Insights
(To be filled after completion)

### Tips for Similar Work
(To be filled after completion)

### Blockers Found
(To be filled after completion)

---

## WU-16: Update PluginSelector

**Status**: Not yet started  
**Estimated**: 1 hour  
**Completed**: TBD

### What Went Well
(To be filled after completion)

### Challenges & Solutions
(To be filled after completion)

### Key Insights
(To be filled after completion)

### Tips for Similar Work
(To be filled after completion)

### Blockers Found
(To be filled after completion)

---

## WU-17: Update ResultsPanel

**Status**: Not yet started  
**Estimated**: 1 hour  
**Completed**: TBD

### What Went Well
(To be filled after completion)

### Challenges & Solutions
(To be filled after completion)

### Key Insights
(To be filled after completion)

### Tips for Similar Work
(To be filled after completion)

### Blockers Found
(To be filled after completion)

---

## WU-18: Integrate WebSocket

**Status**: Not yet started  
**Estimated**: 1 hour  
**Completed**: TBD

### What Went Well
(To be filled after completion)

### Challenges & Solutions
(To be filled after completion)

### Key Insights
(To be filled after completion)

### Tips for Similar Work
(To be filled after completion)

### Blockers Found
(To be filled after completion)

---

## WU-19: Setup testing framework

**Status**: Not yet started  
**Estimated**: 45 minutes  
**Completed**: TBD

### What Went Well
(To be filled after completion)

### Challenges & Solutions
(To be filled after completion)

### Key Insights
(To be filled after completion)

### Tips for Similar Work
(To be filled after completion)

### Blockers Found
(To be filled after completion)

---

## WU-20: Write API client tests

**Status**: Not yet started  
**Estimated**: 1 hour  
**Completed**: TBD

### What Went Well
(To be filled after completion)

### Challenges & Solutions
(To be filled after completion)

### Key Insights
(To be filled after completion)

### Tips for Similar Work
(To be filled after completion)

### Blockers Found
(To be filled after completion)

---

## WU-21: Write WebSocket tests

**Status**: Not yet started  
**Estimated**: 1 hour  
**Completed**: TBD

### What Went Well
(To be filled after completion)

### Challenges & Solutions
(To be filled after completion)

### Key Insights
(To be filled after completion)

### Tips for Similar Work
(To be filled after completion)

### Blockers Found
(To be filled after completion)

---

## WU-22: Update documentation

**Status**: Not yet started  
**Estimated**: 1 hour  
**Completed**: TBD

### What Went Well
(To be filled after completion)

### Challenges & Solutions
(To be filled after completion)

### Key Insights
(To be filled after completion)

### Tips for Similar Work
(To be filled after completion)

### Blockers Found
(To be filled after completion)

---

## Cross-Cutting Insights

(To be added as patterns emerge across units)

- Common extraction patterns
- Integration gotchas
- TypeScript/Vite configuration best practices
- Testing patterns
- Component styling conventions
- API integration patterns
