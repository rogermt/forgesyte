#!/usr/bin/env bash
set -e

echo "=== Phase 6 Expected Test Suite (Canonical) ==="

cat <<EOF
web-ui/src/App.test.tsx
web-ui/src/App.integration.test.tsx
web-ui/src/App.tdd.test.tsx
web-ui/src/components/ResultOverlay.test.tsx
web-ui/src/components/VideoTracker.test.tsx
web-ui/src/components/ImageUpload.test.tsx
web-ui/src/components/ImagePreview.test.tsx
web-ui/src/components/PluginSelector.test.tsx
web-ui/src/components/PluginCard.test.tsx
web-ui/src/components/PluginList.test.tsx
web-ui/src/components/DeviceSelector.test.tsx
web-ui/src/components/ErrorBoundary.test.tsx
web-ui/src/hooks/useVideoProcessor.test.ts
web-ui/src/hooks/useWebSocket.test.ts
web-ui/src/hooks/usePluginManifest.test.ts
web-ui/src/utils/drawDetections.test.ts
web-ui/src/utils/formatTime.test.ts
web-ui/src/utils/validateImage.test.ts
web-ui/src/api/jobClient.test.ts
web-ui/src/api/analyzeImage.test.ts
web-ui/src/api/client.test.ts
web-ui/src/plugins/__tests__/manifest-loading.test.ts
EOF
