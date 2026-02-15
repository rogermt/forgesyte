# ⭐ **PHASE‑16 CONTRIBUTOR EXAM**  
### *20 questions — must pass before contributing to Phase‑16*

---

## **Section A — Architecture (6 questions)**

1. What are the three new subsystems introduced in Phase‑16?  
2. Why must job submission be asynchronous?  
3. Why must the worker process be separate from the API process?  
4. What is the purpose of the job table?  
5. Why must the queue payload contain only `job_id`?  
6. Why must the worker use the Phase‑15 VideoFilePipelineService?

---

## **Section B — Job Lifecycle (6 questions)**

7. What are the four valid job statuses?  
8. What triggers the transition from pending → running?  
9. What triggers the transition from running → completed?  
10. What triggers the transition from running → failed?  
11. What happens if the worker crashes mid‑job?  
12. Why must results be stored in object storage instead of memory?

---

## **Section C — API Behavior (4 questions)**

13. What does `POST /video/submit` return?  
14. When does `GET /video/status/{job_id}` return 404?  
15. When does `GET /video/results/{job_id}` return 404?  
16. Why must progress be coarse (0, 0.5, 1.0)?

---

## **Section D — Governance & Testing (4 questions)**

17. Name two Phase‑17 concepts forbidden in Phase‑16.  
18. Why must the worker tests use a mock queue?  
19. Why must integration tests simulate a full job lifecycle?  
20. Why must the rollback plan remove the job table?

---

If you want, I can generate the **answer key** too.

---



---

Here we go, Roger — the **Phase‑16 deep pack**: answers, state machine, clean interfaces, and a concrete worker implementation.

---

### Phase‑16 contributor exam — answer key

**1. What are the three new subsystems introduced in Phase‑16?**  
Job queue, job table (persistence), worker process.

**2. Why must job submission be asynchronous?**  
Because processing can be long‑running; we can’t block HTTP requests and must decouple client from execution time.

**3. Why must the worker process be separate from the API process?**  
To avoid blocking, allow independent scaling, and prevent heavy workloads from impacting API latency.

**4. What is the purpose of the job table?**  
To persist job state (status, paths, errors) across restarts and allow status/results queries.

**5. Why must the queue payload contain only `job_id`?**  
To keep messages small, deterministic, and avoid duplicating state that already lives in the DB.

**6. Why must the worker use the Phase‑15 VideoFilePipelineService?**  
To reuse the existing, tested batch pipeline and avoid duplicating business logic.

**7. What are the four valid job statuses?**  
`pending`, `running`, `completed`, `failed`.

**8. What triggers the transition from pending → running?**  
The worker dequeues the job and starts processing it.

**9. What triggers the transition from running → completed?**  
The worker finishes processing successfully and stores results.

**10. What triggers the transition from running → failed?**  
The worker encounters an unrecoverable error and records `error_message`.

**11. What happens if the worker crashes mid‑job?**  
The job remains `pending` or `running` (depending on when it crashed) and can be retried or inspected; no status is silently changed.

**12. Why must results be stored in object storage instead of memory?**  
To survive process restarts, support large payloads, and decouple storage from worker memory.

**13. What does `POST /video/submit` return?**  
A JSON object containing `{ "job_id": "<uuid>" }`.

**14. When does `GET /video/status/{job_id}` return 404?**  
When the job_id does not exist in the job table.

**15. When does `GET /video/results/{job_id}` return 404?**  
When the job_id does not exist, or the job is not yet `completed`.

**16. Why must progress be coarse (0, 0.5, 1.0)?**  
To avoid frame‑level tracking complexity and keep Phase‑16 simple and deterministic.

**17. Name two Phase‑17 concepts forbidden in Phase‑16.**  
WebSockets, real‑time streaming, GPU scheduling, distributed workers (any two).

**18. Why must the worker tests use a mock queue?**  
To make tests deterministic, fast, and independent of real queue infrastructure.

**19. Why must integration tests simulate a full job lifecycle?**  
To verify that submit → worker → status → results all work together as designed.

**20. Why must the rollback plan remove the job table?**  
Because Phase‑16 introduces it; rollback must restore a pure Phase‑15 state with no leftover schema.

---