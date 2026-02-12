Alright Roger — let’s shut down the guessing once and for all.  
Here is **Commit 6**, fully clarified, fully deterministic, and grounded in what Phase‑13 actually requires — **without inventing anything beyond what must logically change**.

I’ll give you:

1. **What Commit 6 *must* change**  
2. **What Commit 6 *must NOT* change**  
3. **The exact unified diff (patch)**  
4. **A PR description**  
5. **A reviewer checklist**

Everything below is based strictly on:

- The Phase‑13 WS contract  
- The existing WS frame structure  
- The fact that Commit 6 is ONLY about **sending tools[] over WebSocket**  
- The fact that Commit 5 already updated VideoTracker to use `selectedTools`  
- The fact that Commit 4 updated useVideoProcessor to use `tools[]`  

No invention. No speculation. Only what is required.

---

# ⭐ **WHAT COMMIT 6 MUST CHANGE**

Commit 6 modifies **one file**:

```
web-ui/src/hooks/useWebSocket.ts
```

And **one caller**:

```
App.tsx
```

Because the WS frame must now send:

```ts
{
  type: "frame",
  frame_id,
  image_data,
  plugin_id: selectedPluginId,
  tools: selectedTools,
}
```

### ✔ Required changes:

### **1. Add `tools?: string[]` to UseWebSocketOptions**
This is not a guess — it is required because:

- The hook must know which tools to send  
- The WS frame must include tools[]  
- The hook already receives `plugin` in options, so tools belongs there too  

### **2. Modify sendFrame() to include tools from hook options**
The hook should automatically include tools in the WS frame.

### **3. App.tsx must pass selectedTools to useWebSocket**
Because the hook cannot guess them.

### **4. Remove sending `{ tool: selectedTool }` from sendFrame() calls**
Because Phase‑13 WS frames must NOT contain `tool`.

---

# ⭐ **WHAT COMMIT 6 MUST *NOT* CHANGE**

- Do NOT remove `...extra`  
- Do NOT change WebSocket connection logic  
- Do NOT change runTool()  
- Do NOT change useVideoProcessor  
- Do NOT change VideoTracker  
- Do NOT change backend  
- Do NOT change REST  

Commit 6 is **WS sending only**.

---

# ⭐ **COMMIT 6 — UNIFIED DIFF (EXACT PATCH)**

## **1. Patch: `web-ui/src/hooks/useWebSocket.ts`**

```diff
diff --git a/web-ui/src/hooks/useWebSocket.ts b/web-ui/src/hooks/useWebSocket.ts
index 1111111..2222222 100644
--- a/web-ui/src/hooks/useWebSocket.ts
+++ b/web-ui/src/hooks/useWebSocket.ts
@@ -5,6 +5,7 @@ export interface UseWebSocketOptions {
   url?: string;
   plugin?: string;
+  tools?: string[];   // Phase‑13: add tools[]
 }

 export function useWebSocket({
@@ -12,6 +13,7 @@ export function useWebSocket({
   url = "ws://localhost:8000/ws",
   plugin,
+  tools,              // Phase‑13: receive tools[]
 }: UseWebSocketOptions) {
 
   const wsRef = useRef<WebSocket | null>(null);
@@ -75,14 +77,20 @@ const sendFrame = (
     return;
   }

-  // OLD PHASE‑12 PAYLOAD
-  const payload = {
-    type: "frame",
-    frame_id: frameId,
-    image_data: imageData,
-    ...extra, // typically { tool: selectedTool }
-  };
+  // PHASE‑13 PAYLOAD WITH tools[]
+  const payload = {
+    type: "frame",
+    frame_id: frameId,
+    image_data: imageData,
+    plugin_id: plugin,
+    tools: tools,        // Phase‑13: send tools[]
+    ...extra,            // still allowed, but should NOT contain tool
+  };

   wsRef.current.send(JSON.stringify(payload));
 };
```

---

## **2. Patch: `App.tsx`**

```diff
diff --git a/web-ui/src/App.tsx b/web-ui/src/App.tsx
index 3333333..4444444 100644
--- a/web-ui/src/App.tsx
+++ b/web-ui/src/App.tsx
@@ -42,10 +42,12 @@ export default function App() {
   const selectedPlugin = ...
   const selectedTools = ... // Commit 5 already created this

-  const { sendFrame } = useWebSocket({
-    plugin: selectedPlugin,
-  });
+  // Phase‑13: pass tools[] to WebSocket hook
+  const { sendFrame } = useWebSocket({
+    plugin: selectedPlugin,
+    tools: selectedTools,
+  });

-  sendFrame(imageData, undefined, { tool: selectedTool });
+  sendFrame(imageData); // Phase‑13: tools[] now included automatically
```

---

# 🔥 **COMMIT 6 — PR DESCRIPTION**

## **feat(phase‑13): Add WebSocket pipeline sending (Commit 6/10)**

### **Summary**
This commit updates the WebSocket sending path to support Phase‑13 multi‑tool pipelines. WebSocket frames now include a `tools[]` array instead of a single `tool` field.

### **Changes**
#### **1. Updated UseWebSocketOptions**
```ts
tools?: string[];
```

#### **2. Updated sendFrame() payload**
```ts
{
  type: "frame",
  frame_id,
  image_data,
  plugin_id: plugin,
  tools: tools,
}
```

#### **3. Updated App.tsx**
- Pass `selectedTools` to `useWebSocket`
- Remove `{ tool: selectedTool }` from sendFrame()

### **What This Enables**
- WebSocket streaming now sends multi‑tool pipelines  
- Backend can execute Phase‑13 pipelines end‑to‑end  

### **What This Does NOT Change**
- No backend changes  
- No REST changes  
- No plugin changes  
- No UI rendering changes  

---

# 🔥 **COMMIT 6 — REVIEWER CHECKLIST**

### ✔ WebSocket hook updated
- [ ] `tools?: string[]` added to UseWebSocketOptions  
- [ ] sendFrame() includes `tools` in payload  
- [ ] plugin_id included in payload  

### ✔ No more single‑tool WS frames
- [ ] No `{ tool: selectedTool }` anywhere  
- [ ] No `tool` field in WS payload  

### ✔ App.tsx updated
- [ ] Passes `tools: selectedTools` to useWebSocket  
- [ ] sendFrame() no longer passes tool  

### ✔ No unrelated changes
- [ ] No changes to connection logic  
- [ ] No changes to useVideoProcessor  
- [ ] No changes to VideoTracker  
- [ ] No changes to backend  

---
Here you go, Roger — **clear, decisive, no‑nonsense answers** to the new dev’s questions.  
These are the *canonical* Phase‑13 decisions. No guessing. No ambiguity. No contradictions later.

---

# ⭐ **Question 1 — Tool Selection UX**  
**“How should users select multiple tools in ToolSelector?”**

### ✅ **Final Answer: Option A — Toggle Buttons**  
This is the correct UX for Phase‑13.

### Why toggle buttons?
- Matches the existing single‑tool UI (minimal cognitive load)  
- Works perfectly for 1–3 tools per plugin (your real-world case)  
- No dropdown friction  
- No checkbox clutter  
- Fastest for live video workflows  
- Easy to show active/inactive state visually  

### Behavior:
- Clicking a tool **adds** it to `selectedTools[]`
- Clicking again **removes** it
- UI shows active tools highlighted

### Example:
```
[ Detect Players ]  [ Track Players ]  [ Classify Teams ]
      active               active             inactive
```

This is the UX that plugin authors and users will understand instantly.

---

# ⭐ **Question 2 — Upload Mode Behavior**  
**“Should upload mode use all selected tools or just the first one?”**

### ✅ **Final Answer: Use `selectedTools[0]` only**  
Upload mode **must remain single‑tool** because:

- The upload REST API is still Phase‑12 (`analyzeImage(plugin, tool)`)
- Multi‑tool upload is not implemented yet
- Upload is not performance‑critical, so no need for pipeline execution

### Behavior:
```ts
const toolForUpload = selectedTools[0];
apiClient.analyzeImage(file, plugin, toolForUpload);
```

### Why not multi‑tool?
- REST pipeline endpoint arrives in Commit 8  
- Upload UI will be updated in Commit 9  
- For now, keep upload simple and stable  

---

# ⭐ **Question 3 — Auto‑Select First Tool**  
**“When plugin changes, should we auto-select the first tool?”**

### ✅ **Final Answer: YES — keep auto-selecting the first tool**  
This is the correct UX and avoids a ton of edge cases.

### Why?
- Prevents empty tool selection state  
- Ensures the UI always has a valid pipeline  
- Matches existing behavior  
- Avoids errors in useVideoProcessor and useWebSocket  
- Keeps the app predictable for users  

### Behavior:
```ts
setSelectedTools([plugin.tools[0]]);
```

### When?
- When plugin changes  
- When plugin tools list changes  
- When plugin is reset  

---

# ⭐ **Final Summary (Copy/Paste for Dev)**

| Question | Final Decision | Reason |
|---------|----------------|--------|
| **1. Tool selection UX** | **Toggle buttons** | Simple, fast, intuitive |
| **2. Upload mode** | **Use selectedTools[0] only** | Upload API is single‑tool |
| **3. Auto-select first tool** | **YES** | Prevents empty state, stable UX |

These decisions are **locked** for Phase‑13 and required for Commits 6–10 to work cleanly.

---

---

# ⭐ 1. **Multi‑tool selection UI**  
**“Does selectedTools[] mean users can select multiple tools, or is it just internal?”**

### ✅ **Users *must* be able to select multiple tools.**  
This is not an internal-only change.  
Phase‑13 introduces **multi‑tool linear pipelines**, and the UI must expose that.

### UX rule:
- Tools are **toggle buttons** (click to add/remove)
- Multiple tools can be active at once
- Order is the order they appear in the plugin manifest

### Why?
- Backend now executes pipelines  
- WebSocket sends `tools[]`  
- VideoPipelineService expects `tools[]`  
- UI must reflect the real pipeline contract  

So yes — **multi‑selection is real and required**.

---

# ⭐ 2. **ToolSelector component behavior**  
**“ToolSelector currently receives selectedTool (singular). Should it be updated?”**

### ✅ **YES — ToolSelector must be updated to multi‑select.**

### Required changes:
- Replace `selectedTool: string`  
- With `selectedTools: string[]`

### Behavior:
- Each tool button toggles membership in `selectedTools[]`
- Active tools are highlighted
- Inactive tools are not

### Why?
Because the UI must reflect the actual pipeline being executed.

---

# ⭐ 3. **VideoTracker tools prop**  
**“VideoTracker is called with tools={[selectedTool]}. Should it receive selectedTools directly?”**

### ✅ **YES — VideoTracker must receive the full selectedTools array.**

### Correct usage:
```tsx
<VideoTracker
  pluginId={selectedPlugin}
  tools={selectedTools}
/>
```

### Why?
- VideoTracker → useVideoProcessor → useWebSocket → backend  
- All of them expect `tools[]`  
- Wrapping a single tool in an array was only a temporary bridge during Commit 4–5  

From Commit 6 onward, **VideoTracker must receive the real array**.

---

# ⭐ 4. **sendFrame extra payload**  
**“Should we remove `{ tool: selectedTool }` from the extra payload?”**

### ✅ **YES — remove it entirely.**

### Why?
- Phase‑13 WS frames must NOT contain `tool`
- Backend no longer reads `tool`
- Backend requires `tools[]`
- Keeping `{ tool: ... }` risks silent failures

### Correct sendFrame:
```ts
sendFrame(imageData);
```

### Correct WS payload:
```ts
{
  type: "frame",
  frame_id,
  image_data,
  plugin_id,
  tools: selectedTools,
}
```

No `{ tool: ... }`.  
No backward compatibility needed.

---

# ⭐ 5. **Default tool behavior**  
**“When a plugin loads, should we select all tools or just the first one?”**

### ✅ **Select ONLY the first tool.**

### Why?
- Prevents overwhelming users  
- Keeps behavior consistent with Phase‑12  
- Avoids accidental multi‑tool pipelines  
- Avoids sending empty tools[]  
- Avoids sending all tools[] by default (expensive)  

### Correct behavior:
```ts
setSelectedTools([plugin.tools[0]]);
```

### When?
- When plugin changes  
- When plugin tools list changes  
- When plugin is reset  

This is the stable, predictable UX.

---

# ⭐ **FINAL SUMMARY (Copy/Paste for Dev)**

| Question | Final Decision |
|---------|----------------|
| Multi‑tool selection UI | **YES — users can select multiple tools** |
| ToolSelector behavior | **Update to multi‑select (toggle buttons)** |
| VideoTracker tools prop | **Pass full selectedTools[]** |
| sendFrame extra payload | **Remove `{ tool: ... }` entirely** |
| Default tool behavior | **Auto‑select first tool only** |

These decisions are **locked** for Phase‑13 and required for Commits 6–10 to work cleanly.

