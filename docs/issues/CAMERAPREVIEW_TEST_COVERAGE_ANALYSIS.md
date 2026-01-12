# CameraPreview Component - Test Coverage Analysis

**Component**: `web-ui/src/components/CameraPreview.tsx`  
**Current Coverage**: 45.45% (Lines: 47.61%)  
**Gap to 80%**: +34.55%  
**Lines Missing Tests**: 127, 132, 184-196

---

## Executive Summary

CameraPreview has critical gaps in test coverage because existing tests only validate **styling/rendering**, not **functionality**. The component has:

- ✅ Heading and layout validation (styling)
- ✅ Video element styling checks
- ✅ Canvas element verification
- ❌ **NO tests for camera stream lifecycle** (start/stop)
- ❌ **NO tests for frame capture logic**
- ❌ **NO tests for device enumeration**
- ❌ **NO tests for error handling**
- ❌ **NO tests for media constraints**

---

## Component Functionality Overview

### Critical Logic Not Tested

#### 1. Device Enumeration (Lines 35-48)
```typescript
useEffect(() => {
    navigator.mediaDevices
        .enumerateDevices()
        .then((deviceList) => {
            const videoDevices = deviceList.filter((d) => d.kind === "videoinput");
            setDevices(videoDevices);
            if (!selectedDevice && videoDevices.length > 0) {
                setSelectedDevice(videoDevices[0].deviceId);
            }
        })
        .catch((err) => {
            console.error("Failed to enumerate devices:", err);
        });
}, [selectedDevice]);
```
**Uncovered**: Device filtering, auto-selection logic, error handling on enumeration failure

#### 2. Camera Start (Lines 51-75) - `startCamera()`
```typescript
const startCamera = useCallback(async () => {
    try {
        const constraints: MediaStreamConstraints = {
            video: {
                width: { ideal: width },
                height: { ideal: height },
                deviceId: selectedDevice ? { exact: selectedDevice } : undefined,
            },
        };

        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        streamRef.current = stream;

        if (videoRef.current) {
            videoRef.current.srcObject = stream;
            await videoRef.current.play();
            setIsStreaming(true);
            setError(null);
        }
    } catch (err) {
        console.error("Failed to start camera:", err);
        setError(err instanceof Error ? err.message : "Failed to access camera");
        setIsStreaming(false);
    }
}, [width, height, selectedDevice]);
```
**Uncovered**: 
- Successful stream start
- Error handling on permission denied
- Video element setup
- State transitions

#### 3. Camera Stop (Lines 78-87) - `stopCamera()`
```typescript
const stopCamera = useCallback(() => {
    if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
    }
    if (videoRef.current) {
        videoRef.current.srcObject = null;
    }
    setIsStreaming(false);
}, []);
```
**Uncovered**: 
- Track cleanup
- Stream teardown
- State reset

#### 4. Frame Capture (Lines 90-109) - `captureFrame()`
```typescript
const captureFrame = useCallback(() => {
    if (!videoRef.current || !canvasRef.current || !isStreaming || !enabled) {
        return;
    }

    const canvas = canvasRef.current;
    const video = videoRef.current;
    const ctx = canvas.getContext("2d");

    if (!ctx) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    const dataUrl = canvas.toDataURL("image/jpeg", 0.8);
    const base64Data = dataUrl.split(",")[1];

    onFrame?.(base64Data);
}, [isStreaming, enabled, onFrame]);
```
**Uncovered** (Lines 127, 132, 184-196):
- Frame capture when streaming
- Canvas context handling
- Base64 conversion
- Callback invocation
- Guard conditions (disabled, not streaming)

#### 5. Effect Hooks (Lines 112-135)
- **Effect #1** (112-122): Start/stop camera based on `enabled` prop
- **Effect #2** (125-135): Setup/cleanup frame capture interval

**Uncovered**: All effect behavior including cleanup

#### 6. Device Selector UI (Lines 169-203) - **Lines 184-196**
```typescript
{devices.length > 1 && (
    <div style={{ marginBottom: "12px" }}>
        <label>Camera Device</label>
        <select
            value={selectedDevice}
            onChange={(e) => setSelectedDevice(e.target.value)}
            {/* ...styling... */}
        >
            {devices.map((device) => (
                <option key={device.deviceId} value={device.deviceId}>
                    {device.label || `Camera ${device.deviceId.slice(0, 5)}`}
                </option>
            ))}
        </select>
    </div>
)}
```
**Uncovered**: 
- Device selection change handling
- Multiple device display logic
- Device label fallback

---

## Test Coverage Breakdown

### Currently Tested (Styling Only)
1. ✅ Heading renders
2. ✅ Video element styling
3. ✅ Canvas hidden
4. ✅ Status paragraph exists
5. ✅ Select element styling (when visible)

### Missing Tests (45% gap)

| Feature | Lines | Tests Needed | Priority |
|---------|-------|-------------|----------|
| Device enumeration | 35-48 | 3 | HIGH |
| Camera start | 51-75 | 4 | HIGH |
| Camera stop | 78-87 | 2 | HIGH |
| Frame capture | 90-109 | 5 | HIGH |
| Start/stop effect | 112-122 | 3 | HIGH |
| Capture interval effect | 125-135 | 3 | HIGH |
| Device selector | 184-196 | 3 | MEDIUM |
| Error display | 140-151 | 2 | MEDIUM |

**Total New Tests Needed**: ~25 test cases

---

## Required Test Cases

### Group 1: Device Management (3 tests)
```typescript
describe("device enumeration", () => {
    it("should enumerate video input devices on mount");
    it("should auto-select first device if none selected");
    it("should handle enumeration errors gracefully");
});
```

### Group 2: Camera Lifecycle (6 tests)
```typescript
describe("camera stream lifecycle", () => {
    it("should start camera stream when enabled=true");
    it("should stop camera stream when enabled=false");
    it("should handle getUserMedia errors");
    it("should update isStreaming state on successful start");
    it("should clear error on successful start");
    it("should stop all tracks on cleanup");
});
```

### Group 3: Frame Capture (5 tests)
```typescript
describe("frame capture", () => {
    it("should capture frame at specified interval");
    it("should call onFrame callback with base64 data");
    it("should not capture when disabled");
    it("should not capture when not streaming");
    it("should handle canvas context errors");
});
```

### Group 4: Device Selection (3 tests)
```typescript
describe("device selection", () => {
    it("should show selector when multiple devices available");
    it("should hide selector when only one device");
    it("should update selectedDevice on change");
});
```

### Group 5: Error Handling (2 tests)
```typescript
describe("error handling", () => {
    it("should display error message from getUserMedia");
    it("should apply error styling to error display");
});
```

### Group 6: Effect Dependencies (3 tests)
```typescript
describe("effect cleanup", () => {
    it("should cleanup interval on unmount");
    it("should cleanup camera on unmount");
    it("should restart camera when width/height changes");
});
```

---

## Mock Requirements

To test CameraPreview, you need to mock:

### 1. MediaDevices API
```typescript
const mockGetUserMedia = jest.fn();
const mockEnumerateDevices = jest.fn();

navigator.mediaDevices = {
    getUserMedia: mockGetUserMedia,
    enumerateDevices: mockEnumerateDevices,
};
```

### 2. MediaStream API
```typescript
const mockMediaStream = {
    getTracks: jest.fn(() => [{
        stop: jest.fn(),
        kind: 'video',
    }]),
};

mockGetUserMedia.mockResolvedValue(mockMediaStream);
```

### 3. HTMLVideoElement
```typescript
HTMLVideoElement.prototype.play = jest.fn(async () => {});
HTMLVideoElement.prototype.pause = jest.fn();
Object.defineProperty(HTMLVideoElement.prototype, 'srcObject', {
    set: jest.fn(),
    get: jest.fn(),
});
```

### 4. Canvas API
```typescript
const mockCanvas = {
    getContext: jest.fn(() => ({
        drawImage: jest.fn(),
    })),
};
```

---

## Impact on Issue #17

**WebSocket Error Issue**: While CameraPreview doesn't directly cause the WebSocket error, its untested camera initialization might mask related issues:

- Device enumeration errors could prevent UI from rendering properly
- Camera start/stop lifecycle issues could interfere with WebSocket connection timing
- Frame capture errors could crash the stream handler

**Recommendation**: Fix CameraPreview coverage first, then verify WebSocket connection behavior with fully functional camera component.

---

## Effort Estimate

| Task | Effort | Owner |
|------|--------|-------|
| Setup mocks | 1-2 hours | Agent |
| Write 25 tests | 3-4 hours | Agent |
| Debug + iterate | 1-2 hours | Agent |
| Verify 80% coverage | 0.5 hours | Agent |
| **Total** | **5-8 hours** | - |

---

## Success Criteria

- [ ] CameraPreview coverage reaches 80%+ (from 45%)
- [ ] All 25 test cases pass
- [ ] Mocks properly simulate browser APIs
- [ ] No console errors during test runs
- [ ] Code review approval
- [ ] Merge to main

---

## Related Files
- **Component**: `web-ui/src/components/CameraPreview.tsx`
- **Test File**: `web-ui/src/components/CameraPreview.test.tsx`
- **Related Issue**: #17 (WebSocket Error)
- **Coverage Report**: Generated 2026-01-12 16:52:59 UTC
