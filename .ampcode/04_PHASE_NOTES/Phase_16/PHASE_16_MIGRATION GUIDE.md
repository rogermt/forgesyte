# ⭐ **PHASE‑16 MIGRATION GUIDE**

### **1. Add job table migration**  
- Create migration script  
- Add ORM model  

### **2. Add StorageService**  
- Implement local filesystem backend  

### **3. Add QueueService**  
- Implement in‑memory backend  

### **4. Add job submission endpoint**  
- Validate MP4  
- Save file  
- Create job row  
- Enqueue job_id  

### **5. Add worker process**  
- Pull job_id  
- Mark running  
- Execute pipeline  
- Save results  
- Mark completed  

### **6. Add status + results endpoints**  
- GET /video/status/{job_id}  
- GET /video/results/{job_id}  

### **7. Update governance + CI**  
- Forbidden vocabulary  
- Path validator  
- Smoke test  

### **8. Update documentation**  
- Overview  
- Architecture  
- Testing  
- Rollback  

---