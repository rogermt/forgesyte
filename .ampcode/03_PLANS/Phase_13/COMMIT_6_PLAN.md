# COMMIT 6: UI Tool Selector (Multi-Tool Support)
**Status:** IN PROGRESS
**TDD Workflow:** Test → Code → Verify

Plan for Commit 6: WebSocket Multi-Tool Sending
Based on the PHASE_13_COMMIT_6.md document, here are the exact changes needed:

1. Update App.tsx - Multiple Changes Required
Change 1: Replace selectedTool: string with selectedTools: string[]

Line ~31: Change const [selectedTool, setSelectedTool] = useState<string>(""); to const [selectedTools, setSelectedTools] = useState<string[]>([]);
Change 2: Pass tools: selectedTools to useWebSocket

Line ~105: Add tools: selectedTools, to the useWebSocket options object
Change 3: Remove { tool: selectedTool } from sendFrame calls

Line ~218: Change sendFrame(imageData, undefined, { tool: selectedTool }); to sendFrame(imageData);
Change 4: Update tool selection logic

Line ~160-167: Update the useEffect that auto-selects the first tool to use setSelectedTools([toolList[0]]); instead of setSelectedTool(toolList[0]);
Change 5: Update tool reset when plugin changes

Line ~150-155: Update to use setSelectedTools([]); instead of setSelectedTool("");
Change 6: Update VideoTracker props

Line ~282: Change tools={[selectedTool]} to tools={selectedTools}
Change 7: Update upload mode to use selectedTools[0]

Line ~238: Change const response = await apiClient.analyzeImage(file, selectedPlugin, selectedTool); to use selectedTools[0]
Change 8: Update conditional checks

Line ~241: Change if (!selectedTool) return; to if (selectedTools.length === 0) return;
Line ~278: Change selectedTool && ( to selectedTools.length > 0 && (
2. Update ToolSelector.tsx - Convert to Multi-Select
Change 1: Update props interface

Replace selectedTool: string with selectedTools: string[]
Replace onToolChange: (toolName: string) => void with onToolChange: (toolNames: string[]) => void
Change 2: Replace dropdown with toggle buttons

Replace the <select> element with a list of toggle buttons
Each button toggles membership in selectedTools[]
Active tools are highlighted
Change 3: Update event handler

Change handleChange to toggle tool in the array instead of replacing
Change 4: Update selectedToolData

Show info for first selected tool, or none if empty
3. Update App.tdd.test.tsx - Update Tests
Change 1: Update ToolSelector mock

Replace selectedTool: string with selectedTools: string[]
Update button handlers to toggle tools in array
Change 2: Update test assertions

Change assertions to check for tools array in WebSocket payload instead of tool in extra
Update to expect sendFrame(imageData) without extra parameter
Update to check selectedTools array instead of selectedTool string
Change 3: Remove { tool: ... } checks

Tests should NOT check for { tool: ... } in sendFrame calls
Instead verify that tools is passed to useWebSocket
4. Verify useWebSocket.ts - Already Complete
The useWebSocket.ts file is already correctly updated with:

tools?: string[] in UseWebSocketOptions interface
tools included in the WebSocket frame payload
plugin_id included in the payload
Summary of Changes
File	Changes
App.tsx	8 changes: switch to selectedTools[], pass to hook, remove { tool: ... }, update VideoTracker, update upload mode
ToolSelector.tsx	4 changes: multi-select props, toggle buttons UI, toggle logic, update info display
App.tdd.test.tsx	3 changes: update mocks, update assertions, remove { tool: ... } checks
useWebSocket.ts	✓ Already complete (no changes needed)

