#!/bin/bash

echo "=== Phase 17 Cleanup: Removing Legacy Phase 10 Architecture ==="

# Legacy Components
rm -f src/components/PluginSelector.tsx
rm -f src/components/ToolSelector.tsx
rm -f src/components/ResultsPanel.tsx
rm -f src/components/PluginInspector.tsx
rm -f src/components/RecordButton.tsx
rm -f src/components/OverlayToggles.tsx
rm -f src/components/ConfidenceSlider.tsx
rm -f src/components/ConfigPanel.tsx
rm -f src/components/DeviceSelector.tsx
rm -f src/components/FPSSlider.tsx
rm -f src/components/RadarView.tsx
rm -f src/components/LoadingSpinner.tsx
rm -f src/components/ProgressBar.tsx
rm -f src/components/BoundingBoxOverlay.tsx
rm -f src/components/OverlayRenderer.tsx
rm -f src/components/ResultOverlay.tsx
rm -f src/components/ErrorBanner.tsx

# Legacy Hooks
rm -f src/hooks/useManifest.ts

# Legacy Utils
rm -f src/utils/detectToolType.ts
rm -f src/utils/runTool.ts
rm -f src/utils/drawDetections.ts

# Legacy Types
rm -f src/types/plugin.ts
rm -f src/types/pipeline_graph.ts

# Legacy Directories
rm -rf src/components/plugins
rm -rf src/components/tools
rm -rf src/components/upload

# Legacy Tests
rm -f src/components/PluginSelector.test.tsx
rm -f src/components/ToolSelector.test.tsx
rm -f src/components/ResultsPanel.test.tsx
rm -f src/components/ResultsPanel.plugin.test.tsx
rm -f src/components/RecordButton.test.tsx
rm -f src/components/OverlayToggles.test.tsx
rm -f src/components/ConfidenceSlider.test.tsx
rm -f src/components/ConfigPanel.test.tsx
rm -f src/components/LoadingSpinner.test.tsx
rm -f src/components/ProgressBar.test.tsx
rm -f src/components/BoundingBoxOverlay.test.tsx
rm -f src/components/OverlayRenderer.test.tsx
rm -f src/components/ResultOverlay.test.tsx

# Legacy Artifacts
rm -f src/components/VideoTracker.test.tsx.skipped
rm -f src/stories/OverlayRenderer.stories.tsx
rm -f src/stories/RealtimeOverlay.stories.tsx
rm -f src/RealtimeOverlay.tsx
rm -f src/tests/noLegacyPluginEndpoint.test.ts

echo "=== Cleanup Complete ==="