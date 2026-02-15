# ⭐ **PHASE‑16 CI WORKFLOW**

### **Triggers**
- PRs touching `server/**`, `server/tools/**`, `scripts/**`

### **Steps**
1. Install dependencies  
2. Validate plugins  
3. Validate pipelines  
4. Validate governance (Phase‑16 rules)  
5. Run unit tests  
6. Run integration tests  
7. Run worker tests  
8. Run smoke test  

### **Smoke Test**
1. validate_plugins  
2. validate_pipelines  
3. validate_video_batch_path  
4. pytest (unit + integration + worker)  

---
