# Task 6.3 — Overlay Toggles Implementation

## Plan

### Information Gathered
- **ResultOverlay.tsx**: Currently uses `showLabels`/`showConfidence` props instead of 5-layer toggle architecture
- **VideoTracker.tsx**: Passes `showLabels`/`showConfidence` instead of `overlayToggles` to the drawing function
- **OverlayToggles.tsx**: Exists but NOT used in VideoTracker; has different interface (`VisibleLayers` without `tracking`)
- The issue specifies a clean architecture where VideoTracker owns state and ResultOverlay is a pure function

### Plan

1. **Update ResultOverlay.tsx**:
   - Add `overlayToggles` prop to `DrawDetectionsParams` and `ResultOverlayProps`
   - Add conditional drawing for each layer:
     - `players` → bounding boxes + labels
     - `tracking` → track IDs
     - `ball` → ball marker
     - `pitch` → pitch lines
     - `radar` → radar points
   - Remove `showLabels`/`showConfidence` props (replaced by overlayToggles)

2. **Update VideoTracker.tsx**:
   - Import `ResultOverlay` function
   - Pass `overlayToggles` to the ResultOverlay call in useEffect
   - Update the drawDetections call to use overlayToggles instead of showLabels/showConfidence

3. **Add Test Suite to VideoTracker.test.tsx**:
   - Add integration tests for each toggle (players, tracking, ball, pitch, radar)
   - Tests verify that VideoTracker calls ResultOverlay with correct toggle state

### Dependent Files to be Edited
- `web-ui/src/components/ResultOverlay.tsx`
- `web-ui/src/components/VideoTracker.tsx`
- `web-ui/src/components/VideoTracker.test.tsx`

### Followup Steps
- Run the test suite to verify implementation
- Manual verification per sign-off criteria

## Implementation Progress

### Step 1: Update ResultOverlay.tsx
- [x] Add overlayToggles to DrawDetectionsParams interface
- [x] Add overlayToggles to ResultOverlayProps interface  
- [x] Update drawDetections to use overlayToggles for conditional drawing
- [x] Update ResultOverlay component to use overlayToggles

### Step 2: Update VideoTracker.tsx
- [x] Import drawDetections function and OverlayToggles type
- [x] Remove duplicate OverlayToggles interface
- [x] Pass overlayToggles to drawDetections in useEffect

### Step 3: Add Test Suite to VideoTracker.test.tsx
- [x] Add overlay toggles integration test suite
- [x] Add tests for each toggle (players, tracking, ball, pitch, radar)
- [x] All 38 tests pass for VideoTracker

### Step 4: Testing
- [x] Run test suite (VideoTracker: 38/38 passing)
- [x] ResultOverlay: 14/18 passing (4 Image loading tests skipped due to jsdom limitations)

## Implementation Summary

### Files Modified:

1. **ResultOverlay.tsx**:
   - Added `OverlayToggles` interface with 5 toggles: `players`, `tracking`, `ball`, `pitch`, `radar`
   - Updated `DrawDetectionsParams` and `ResultOverlayProps` to use `overlayToggles`
   - Added conditional drawing logic for each layer:
     - `players`: bounding boxes + labels
     - `tracking`: track IDs
     - `ball`: ball marker (circle)
     - `pitch`: pitch lines + annotated frame
     - `radar`: radar overlay
   - Removed deprecated `showLabels` and `showConfidence` props

2. **VideoTracker.tsx**:
   - Updated import to use `drawDetections` and `OverlayToggles` from ResultOverlay
   - Removed duplicate `OverlayToggles` interface
   - Updated `useEffect` to pass `overlayToggles` and `pitchLines` to `drawDetections`

3. **VideoTracker.test.tsx**:
   - Added 7 new overlay toggle tests covering:
     - Individual toggle on/off for each layer
     - Toggles are independent (no side effects)
     - Toggle re-enabling

4. **ResultOverlay.test.tsx**:
   - Updated tests to use new `overlayToggles` prop
   - Added tests for each toggle layer behavior
   - 14/18 tests passing (4 Image loading tests skipped due to jsdom limitations)

