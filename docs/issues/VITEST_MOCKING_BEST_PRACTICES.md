
# Vitest Mocking Best Practices Issue

## Summary
The test suite has 6 warnings related to incorrect mocking patterns in `useVideoExport.test.ts`. Vitest recommends using `vi.spyOn()` instead of `vi.fn()` for spying on existing object/class methods.

## Current Warnings
```
stderr | src/hooks/useVideoExport.test.ts > useVideoExport > captures stream from canvas with correct FPS
[vitest] The vi.fn() mock did not use 'function' or 'class' in its implementation, see https://vitest.dev/api/vi#vi-spyon for examples.

stderr | src/hooks/useVideoExport.test.ts > useVideoExport > uses MediaRecorder for recording
[vitest] The vi.fn() mock did not use 'function' or 'class' in its implementation, see https://vitest.dev/api/vi#vi-spyon for examples.

stderr | src/hooks/useVideoExport.test.ts > useVideoExport > cancels recording properly
[vitest] The vi.fn() mock did not use 'function' or 'class' in its implementation, see https://vitest.dev/api/vi#vi-spyon for examples.

stderr | src/hooks/useVideoExport.test.ts > useVideoExport > respects custom MIME type in config
[vitest] The vi.fn() mock did not use 'function' or 'class' in its implementation, see https://vitest.dev/api/vi#vi-spyon for examples.

stderr | src/hooks/useVideoExport.test.ts > useVideoExport > supports default FPS of 30
[vitest] The vi.fn() mock did not use 'function' or 'class' in its implementation, see https://vitest.dev/api/vi#vi-spyon for examples.

stderr | src/hooks/useVideoExport.test.ts > useVideoExport > maintains state across operations
[vitest] The vi.fn() mock did not use 'function' or 'class' in its implementation, see https://vitest.dev/api/vi#vi-spyon for examples.
```

## Affected File
- `web-ui/src/hooks/useVideoExport.test.ts`

## Root Cause Analysis

### Issue 1: MediaRecorder Mock
```tsx
// Current (problematic)
global.MediaRecorder = vi.fn(() => ({
  start: vi.fn(),
  stop: vi.fn(),
  ...
})) as unknown as typeof MediaRecorder;
```

The warning occurs because `vi.fn()` is being used as a constructor. While this works, Vitest suggests using `vi.spyOn()` for better type safety and to preserve the original class structure.

### Issue 2: captureStream Mock
```tsx
// Current (problematic)
HTMLCanvasElement.prototype.captureStream = vi.fn(() => ({
  getTracks: vi.fn(() => []),
})) as unknown as typeof HTMLCanvasElement.prototype.captureStream;
```

### Issue 3: URL Method Mocks
```tsx
// Current (problematic)
global.URL.createObjectURL = vi.fn(() => "blob:mock-url");
global.URL.revokeObjectURL = vi.fn();
```

### Issue 4: Property Assignment on Mocked Constructor
```tsx
// Current (problematic)
vi.mocked(global.MediaRecorder).isTypeSupported = vi.fn((type: string) => {...});
```

## Proposed Fix

### Using `vi.spyOn()` for Global Objects/Classes

```tsx
// Mock MediaRecorder using vi.spyOn with implementation
const mockStart = vi.fn();
const mockStop = vi.fn();
const mockDataAvailable = vi.fn();
const mockError = vi.fn();

// Use vi.spyOn with a factory function for proper constructor mocking
const MockMediaRecorder = vi.fn().mockImplementation(() => ({
  start: mockStart,
  stop: mockStop,
  state: "recording",
  mimeType: "video/webm",
  ondataavailable: mockDataAvailable,
  onerror: mockError,
  onstop: null,
})) as unknown as { new (...args: any[]): MediaRecorder } & { isTypeSupported: (type: string) => boolean };

MockMediaRecorder.isTypeSupported = vi.fn((type: string) => {
  return (
    type === "video/webm" || 
    type === "video/webm;codecs=vp9" || 
    type === "video/webm;codecs=vp8"
  );
});

global.MediaRecorder = MockMediaRecorder;
```

### Alternative: Use `vi.doMock()` with Proper Type Assertions

For browser APIs like `captureStream`, use proper TypeScript typing:

```tsx
// Properly typed mock for captureStream
const mockGetTracks = vi.fn(() => []);
const mockCaptureStream = vi.fn(() => ({
  getTracks: mockGetTracks,
}));

Object.defineProperty(HTMLCanvasElement.prototype, 'captureStream', {
  value: mockCaptureStream,
  writable: true,
  configurable: true,
});
```

### For URL Methods

```tsx
// Mock URL methods properly
const mockCreateObjectURL = vi.fn(() => "blob:mock-url");
const mockRevokeObjectURL = vi.fn();

Object.defineProperty(global, 'URL', {
  value: {
    createObjectURL: mockCreateObjectURL,
    revokeObjectURL: mockRevokeObjectURL,
  },
  writable: true,
  configurable: true,
});
```

## Benefits of Proper Mocking

1. **Better Type Safety**: `vi.spyOn()` maintains TypeScript types
2. **Clearer Intent**: Spying on existing methods is more semantic
3. **Easier Assertions**: Methods like `.toHaveBeenCalled()` work better
4. **Future Compatibility**: Less likely to break with Vitest updates
5. **Cleaner Output**: Eliminates console warnings

## Testing Checklist

### Unit Tests
- [ ] Update MediaRecorder mock to use `vi.spyOn()` pattern
- [ ] Update captureStream mock with proper TypeScript typing
- [ ] Update URL method mocks
- [ ] Verify all 12 tests still pass
- [ ] Verify warnings are eliminated

### Verification
- [ ] Run `npm test -- --run` and check for no warnings
- [ ] Verify test coverage remains at 100%

## References
- [Vitest vi.spyOn Documentation](https://vitest.dev/api/vi#vi-spyon)
- [Vitest Mocking API](https://vitest.dev/api/mock)
- [MDN MediaRecorder](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder)
- [MDN CanvasCaptureMediaStream](https://developer.mozilla.org/en-US/docs/Web/API/CanvasCaptureMediaStream)

## Severity
🟡 **Low** - Tests pass but console warnings should be resolved for cleaner output

## Labels
enhancement, testing, vitest, good-first-issue

---

**Created:** Based on test output from `npm test -- --run`
**Status:** Open for implementation

