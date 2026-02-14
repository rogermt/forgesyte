# ⭐ **PHASE‑16 TEST PLAN**

### **Unit Tests**
- Job model  
- QueueService  
- StorageService  
- Worker state transitions  

### **Integration Tests**
- Submit job → job row created  
- Worker processes job → results stored  
- Status transitions  
- Results retrieval  

### **System Tests**
- Full lifecycle: submit → worker → status → results  

### **Fuzz Tests**
- Corrupted MP4  
- Missing job_id  
- Invalid job_id  

### **Stress Tests**
- 1000 jobs queued  
- Worker throughput