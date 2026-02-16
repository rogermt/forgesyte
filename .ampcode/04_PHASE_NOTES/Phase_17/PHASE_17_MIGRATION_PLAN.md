# ⭐ 3. Migration Plan: Phase‑10 → Phase‑17

### **Goal**
Move from plugin‑based realtime (Phase‑10) to streaming realtime (Phase‑17) without breaking existing features.

---

## **Step 1 — Introduce Phase‑17 as the new canonical realtime API**
- `useRealtime.ts` now exports **Phase‑17**  
- Phase‑10 hooks moved to `useRealtimeLegacy.ts`

---

## **Step 2 — Update RealtimeContext**
- Use Phase‑17 `useRealtime`  
- Remove Phase‑10 assumptions

---

## **Step 3 — Update components**
Replace:

```ts
import { useRealtime } from "./RealtimeContext";
```

with:

```ts
import { useRealtimeContext } from "./RealtimeContext";
```

And use:

```ts
const { state, connect, disconnect, sendFrame } = useRealtimeContext();
```

---

## **Step 4 — Update tests**
Tests now import:

```ts
import { useRealtime } from "./useRealtime";
```

And mock:

```ts
vi.mock("./useRealtime", () => ({
  useRealtime: () => mockRealtime,
}));
```

---

## **Step 5 — Deprecate Phase‑10**
Move Phase‑10 hooks into:

```
src/realtime/useRealtimeLegacy.ts
```

Mark with:

```ts
/** @deprecated Phase 10 legacy realtime system */
```

---

## **Step 6 — Remove Phase‑10 usage**
Search for:

- `useRealtimeConnection`
- `useRealtimeMessages`
- `useProgress`
- `usePluginTimings`

Replace with Phase‑17 equivalents.

---

## **Step 7 — Delete Phase‑10 after Phase‑17 stabilizes**
Once all components migrate, remove:

- `useRealtimeLegacy.ts`
- Phase‑10 message bus
- Phase‑10 plugin timings

---

# ⭐ 4. Diff‑Style Patch (Paste Directly Into Repo)

Here is the exact patch you can apply:

```
--- a/src/realtime/useRealtime.ts
+++ b/src/realtime/useRealtime.ts
@@ -1,10 +1,10 @@
- import { useRealtime } from './RealtimeContext';
+ // Phase 17 replaces Phase 10 realtime
+ // Remove import of useRealtime from RealtimeContext

+ export function useRealtime(options = {}) {
+   return useRealtimeStreaming(options);
+ }

- export function useRealtimeConnection() {
-   const { state, connect, disconnect } = useRealtime();
-   ...
- }
+ // Move Phase 10 hooks to legacy file
+ export {
+   useRealtimeConnection as useLegacyRealtimeConnection,
+   useRealtimeMessages as useLegacyRealtimeMessages,
+   useProgress as useLegacyProgress,
+   usePluginTimings as useLegacyPluginTimings,
+ } from "./useRealtimeLegacy";

--- a/src/realtime/RealtimeContext.tsx
+++ b/src/realtime/RealtimeContext.tsx
@@ -1,10 +1,10 @@
- import { useRealtime } from "./RealtimeContext";
+ import { useRealtime } from "./useRealtime";

 const RealtimeContext = createContext(null);

 export const RealtimeProvider = ({ children }) => {
-   const realtime = useRealtimeConnection();
+   const realtime = useRealtime();

   return (
     <RealtimeContext.Provider value={realtime}>
```

This patch:

- Removes the incorrect import  
- Makes Phase‑17 the canonical realtime hook  
- Fixes the context  
- Moves Phase‑10 to legacy  

---

