# 📘 **UI_PLUGIN_MANAGER.md**  
### *Client‑Side Plugin Discovery & Execution Architecture*

The Web‑UI in ForgeSyte is a **dynamic plugin host**.  
It does not contain plugin‑specific logic.  
Instead, it discovers plugins from the server and executes their tools generically.

This document explains the **UI Plugin Manager**, the central module that powers this behavior.

---

# 🧭 Purpose

The UI Plugin Manager is responsible for:

- Fetching plugin metadata from the server  
- Caching plugin + tool information  
- Exposing a typed API to React components  
- Driving dynamic rendering in the UI  
- Ensuring no plugin‑specific code exists in the frontend  

It is the **single source of truth** for plugin information on the client.

---

# 🏗️ Responsibilities

### ✔ 1. Fetch plugin metadata  
From:

```
GET /v1/plugins
```

Metadata includes:

- plugin name  
- description  
- version  
- tools  
- tool schemas (input/output)  

### ✔ 2. Cache plugin list  
Stored in memory (React context, Zustand, or simple module‑level cache).

### ✔ 3. Expose helper functions

```ts
getPlugins()
getPlugin(pluginName)
getTools(pluginName)
getToolSchema(pluginName, toolName)
```

### ✔ 4. Drive UI components  
Used by:

- `PluginSelector`  
- `ToolSelector`  
- `ResultsPanel`  
- `useVideoProcessor`  
- `runTool()`  

### ✔ 5. Enforce plugin‑agnostic UI  
No hardcoded plugin names.  
No plugin‑specific React components.

---

# 🧩 Example Implementation (TypeScript)

```ts
// uiPluginManager.ts

let pluginCache: PluginMetadata[] | null = null;

export async function fetchPlugins(): Promise<PluginMetadata[]> {
  if (pluginCache) return pluginCache;

  const res = await fetch("/v1/plugins");
  const data = await res.json();
  pluginCache = data.plugins;
  return pluginCache;
}

export function getPlugins(): PluginMetadata[] {
  if (!pluginCache) throw new Error("Plugins not loaded");
  return pluginCache;
}

export function getPlugin(name: string): PluginMetadata | undefined {
  return getPlugins().find(p => p.name === name);
}

export function getTools(pluginName: string) {
  return getPlugin(pluginName)?.tools ?? {};
}

export function getToolSchema(pluginName: string, toolName: string) {
  return getTools(pluginName)[toolName];
}
```

---

# 🧠 Architectural Invariants

The UI Plugin Manager enforces:

- **No plugin‑specific UI logic**  
- **No hardcoded plugin names**  
- **All plugins discovered dynamically**  
- **All tools executed via `runTool()`**  
- **All results rendered generically**  

This ensures the Web‑UI remains future‑proof and plugin‑agnostic.

---

# 🧪 Testing Strategy

Tests should verify:

- Plugin metadata is fetched correctly  
- PluginSelector renders dynamic list  
- getTools() returns correct tool list  
- runTool() is called with correct args  
- ResultsPanel renders generic fields  

---

# 🎯 Summary

The UI Plugin Manager is the backbone of ForgeSyte’s dynamic plugin ecosystem.  
It enables the Web‑UI to support new plugins **without any code changes**, making the system scalable, maintainable, and future‑proof.

---

# 🖼️ **Diagram‑Only Version (For Onboarding Decks)**  
### *Clean, visual, and ready for slides*

```text
                     ┌──────────────────────────────────────────┐
                     │                Web‑UI                    │
                     │     (React • Dynamic Plugin Host)        │
                     └───────────────────────┬──────────────────┘
                                             │
                                             │ Fetch plugin list
                                             │ GET /v1/plugins
                                             ▼
                     ┌──────────────────────────────────────────┐
                     │           UI Plugin Manager              │
                     │──────────────────────────────────────────│
                     │ • Cache plugin metadata                  │
                     │ • Expose getPlugins(), getTools()        │
                     │ • Provide tool schemas                   │
                     │ • No hardcoded plugin names              │
                     └───────────────────────┬──────────────────┘
                                             │
                                             │ User selects plugin + tool
                                             ▼
                     ┌──────────────────────────────────────────┐
                     │           PluginSelector.tsx             │
                     │──────────────────────────────────────────│
                     │ • Renders plugin list                    │
                     │ • Renders tool list                      │
                     │ • Emits selection                        │
                     └───────────────────────┬──────────────────┘
                                             │
                                             │ Execute tool
                                             │ POST /v1/plugins/<p>/tools/<t>/run
                                             ▼
                     ┌──────────────────────────────────────────┐
                     │               runTool()                  │
                     │──────────────────────────────────────────│
                     │ • Unified tool executor                  │
                     │ • Logging + retries                      │
                     │ • Error normalization                    │
                     └───────────────────────┬──────────────────┘
                                             │
                                             │ JSON result
                                             ▼
                     ┌──────────────────────────────────────────┐
                     │            ResultsPanel.tsx              │
                     │──────────────────────────────────────────│
                     │ • Generic rendering                      │
                     │ • text / boxes / labels / errors         │
                     │ • No plugin‑specific logic               │
                     └──────────────────────────────────────────┘
```

---

