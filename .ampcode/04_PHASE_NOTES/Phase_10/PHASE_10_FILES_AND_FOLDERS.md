Absolutely, Roger — and you’re **100% right** to flag this.

Using a directory name like:

```
server/tests/phase10/
```

is **NOT acceptable** in your governance model because:

- “Phase 10” is a **project milestone**, not a behavior  
- Test folders must be **descriptive of functionality**, not tied to a phase  
- Phase‑based naming creates **drift**, **ambiguity**, and **future maintenance debt**  
- It violates your repo philosophy:  
  **“Names describe behavior, not chronology.”**

You caught this early — perfect timing.

Let’s fix it cleanly and mechanically.

---

# ⭐ Corrected Test Directory Naming (Aligned With Your Governance Rules)

Here is the **canonical renaming** that preserves all Phase 10 test intent while making the directory structure behavior‑driven and future‑proof.

## 🔧 Replace:

```
server/tests/phase10/
```

## ✅ With descriptive, behavior‑based directories:

### **1. Real‑time endpoint tests**
```
server/tests/test_realtime_endpoint/
```

### **2. Extended job model tests**
```
server/tests/test_extended_job_model/
```

### **3. Plugin timing + inspector tests**
```
server/tests/test_plugin_inspector/
```

### **4. Connection manager tests**
```
server/tests/test_connection_manager/
```

### **5. ToolRunner integration tests**
```
server/tests/test_toolrunner_realtime/
```

This gives you **five behavior‑driven test suites**, each mapping directly to a Phase 10 feature, without ever encoding the phase name.

---

# ⭐ Corrected Filenames (Authoritative + Behavior‑Based)

Your authoritative filenames remain valid — we simply relocate them:

### **Realtime endpoint**
```
server/tests/test_realtime_endpoint/test_realtime_endpoint.py
```

### **Extended job model**
```
server/tests/test_extended_job_model/test_job_progress_field.py
server/tests/test_extended_job_model/test_plugin_timing_field.py
```

### **Inspector service**
```
server/tests/test_plugin_inspector/test_inspector_service.py
```

### **Connection manager**
```
server/tests/test_connection_manager/test_connection_manager.py
```

### **ToolRunner**
```
server/tests/test_toolrunner_realtime/test_toolrunner_realtime.py
```

This structure is:

- deterministic  
- descriptive  
- future‑proof  
- aligned with your governance rules  
- aligned with your Phase‑10 RED tests  
- aligned with your “names describe behavior, not phases” philosophy  

---

# ⭐ Updated Frontend Test Structure (Same Principle)

Replace:

```
web-ui/tests/phase10/
```

With:

```
web-ui/tests/realtime_endpoint/
web-ui/tests/progress_bar/
web-ui/tests/plugin_inspector/
web-ui/tests/realtime_client/
web-ui/tests/realtime_context/
```

Each folder contains exactly one authoritative test file.

---

# ⭐ Why This Fix Is Correct

### ✔ Eliminates phase‑based naming  
### ✔ Makes tests behavior‑driven  
### ✔ Prevents drift in Phase 11+  
### ✔ Matches your repo philosophy  
### ✔ Keeps authoritative filenames intact  
### ✔ Makes CI + test discovery cleaner  
### ✔ Makes future contributors safer  

This is exactly the kind of mechanical guardrail you build your repo around.

---

# ⭐ If you want, I can now generate:

### 🔹 A **migration script** to rename all Phase 10 test directories  
### 🔹 A **commit message + PR description** for the rename  
### 🔹 A **governance rule** banning phase‑based directory names  
### 🔹 A **repo‑wide scanner** to detect phase‑based naming drift  

Just tell me which one you want.