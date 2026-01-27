# Implementation Plan: Issue #101 - Unify OCR + YOLO Flows

## Overview

This plan implements four key improvements to unify and enhance the analysis flow:

1. **Unified Tool Runner** - Create `runTool.ts` utility to replace divergent fetch patterns in OCR and YOLO flows
2. **Manifest Regression Test** - Ensure manifest is always fetched when a plugin is selected
3. **Logging Wrapper** - Add structured logging for `processFrame()` calls
4. **Retry Wrapper** - Add exponential backoff retry for failed analysis

## Types

### New Types for runTool

```typescript
// web-ui/src/utils/runTool.ts

export interface RunToolOptions {
  pluginId: string;
  toolName: string;
  args: Record<string, unknown>;
}

export interface RunToolResult {
  result: Record<string, unknown>;
  success: boolean;
  error?: string;
}

export interface LoggingContext {
  pluginId: string;
  toolName: string;
  endpoint: string;
  attempt?: number;
  maxRetries?: number;
}

export interface RetryOptions {
  maxRetries?: number;
  baseDelayMs?: number;
  maxDelayMs?: number;
  backoffMultiplier?: number;
}
```

### New Types for Logging

```typescript
// web-ui/src/hooks/useVideoProcessor.ts (additions)

export interface ProcessFrameLogEntry {
  timestamp: number;
  pluginId: string;
  toolName: string;
  durationMs: number;
  success: boolean;
  error?: string;
  retryCount: number;
}

export interface ProcessFrameMetrics {
  totalFrames: number;
  successfulFrames: number;
  failedFrames: number;
  averageDurationMs: number;
  lastError?: string;
}
```

## Files

### New Files to Create

1. **`web-ui/src/utils/runTool.ts`** - Shared tool runner utility
2. **`web-ui/src/utils/runTool.test.ts`** - Tests for runTool
3. **`web-ui/src/hooks/useVideoProcessor.types.ts`** - TypeScript type definitions

### Existing Files to Modify

1. **`web-ui/src/hooks/useVideoProcessor.ts`** - Add logging wrapper, retry logic, use runTool
2. **`web-ui/src/hooks/useVideoProcessor.test.ts`** - Add tests for logging and retry
3. **`web-ui/src/hooks/useManifest.test.ts`** - Add manifest regression test
4. **`web-ui/src/api/client.ts`** - Optionally integrate runTool for `runPluginTool`

### Files to Delete (after verification)

- None

## Functions

### New Functions

#### runTool (in `web-ui/src/utils/runTool.ts`)

```typescript
export async function runTool({
  pluginId,
  toolName,
  args,
}: RunToolOptions): Promise<RunToolResult>
```

**Purpose**: Unified tool execution with logging and retry logic

**Parameters**:
- `pluginId`: Plugin identifier (e.g., "forgesyte-yolo-tracker")
- `toolName`: Tool name (e.g., "player_detection")
- `args`: Tool arguments matching manifest input schema

**Returns**: `{ result, success, error? }`

**Throws**: Never - errors are captured in result

#### withLogging (in `web-ui/src/utils/runTool.ts`)

```typescript
export function withLogging<T extends (...args: unknown[]) => Promise<unknown>>(
  fn: T,
  context: LoggingContext
): T
```

**Purpose**: Wrapper that adds structured logging to async functions

#### withRetry (in `web-ui/src/utils/runTool.ts`)

```typescript
export function withRetry<T>(
  fn: () => Promise<T>,
  options?: RetryOptions
): Promise<T>
```

**Purpose**: Wrapper that adds exponential backoff retry logic

### Modified Functions

#### processFrame (in `web-ui/src/hooks/useVideoProcessor.ts`)

**Current**: Inline fetch with retry, minimal logging

**Changes**:
- Replace inline fetch with `runTool()`
- Add `withLogging()` wrapper
- Add `withRetry()` wrapper
- Log frame metrics to state

**New signature**: No change (async function)

## Classes

### No class modifications

This implementation uses functional utilities and hooks only.

## Dependencies

### No new packages required

The implementation uses existing:
- `fetch` API (built-in)
- `performance.now()` (built-in)
- Vitest for testing

### Configuration Updates

None required.

## Testing

### Test Files to Create/Modify

#### New: `web-ui/src/utils/runTool.test.ts`

```typescript
describe("runTool", () => {
  it("should call correct endpoint with args");
  it("should return result on success");
  it("should return error on failure");
  it("should include logging output");
});

describe("withLogging", () => {
  it("should log before and after function call");
  it("should include timing information");
});

describe("withRetry", () => {
  it("should retry on failure");
  it("should respect maxRetries option");
  it("should use exponential backoff");
  it("should throw after max retries exhausted");
});
```

#### Modified: `web-ui/src/hooks/useVideoProcessor.test.ts`

**Add new test cases**:
```typescript
it("should log frame processing metrics", async () => {
  // Verify logging calls
});

it("should retry failed analysis with backoff", async () => {
  // Verify retry behavior
});

it("should emit metrics on frame completion", async () => {
  // Verify metrics collection
});
```

#### Modified: `web-ui/src/hooks/useManifest.test.ts`

**Add regression test**:
```typescript
it("should always fetch manifest when pluginId changes", async () => {
  // Verify manifest is fetched even with same ID after cache expires
});

it("should not use stale cache", async () => {
  // Verify cache invalidation behavior
});
```

### Test Strategy

1. **Unit Tests**: Test runTool, withLogging, withRetry in isolation
2. **Integration Tests**: Test useVideoProcessor with mocked fetch
3. **Regression Tests**: Ensure manifest is always fetched when expected
4. **Metric Tests**: Verify logging output format

## Implementation Order

1. **Create type definitions** - `web-ui/src/hooks/useVideoProcessor.types.ts`
2. **Create runTool utility** - `web-ui/src/utils/runTool.ts`
3. **Create runTool tests** - `web-ui/src/utils/runTool.test.ts`
4. **Update useVideoProcessor** - Integrate runTool, add logging, add retry
5. **Add useVideoProcessor tests** - Test logging and retry behavior
6. **Add manifest regression test** - Ensure manifest is always fetched
7. **Run all tests** - Verify implementation
8. **Verify build** - Run `npm run build`

## Task Progress

task_progress Items:
- [ ] Step 1: Create type definitions file (useVideoProcessor.types.ts)
- [ ] Step 2: Create runTool utility with logging and retry (runTool.ts)
- [ ] Step 3: Create unit tests for runTool (runTool.test.ts)
- [ ] Step 4: Update useVideoProcessor.ts to use runTool, logging, retry
- [ ] Step 5: Add logging and retry tests to useVideoProcessor.test.ts
- [ ] Step 6: Add manifest regression test to useManifest.test.ts
- [ ] Step 7: Run full test suite to verify implementation
- [ ] Step 8: Verify build passes with `npm run build`

