
# ⭐ **PHASE‑16 FOLDER STRUCTURE**  
### *Authoritative directory layout for the entire phase*

```
.ampcode/
└── 04_PHASE_NOTES/
    └── Phase_16/
        ├── 00_OVERVIEW.md
        ├── 01_USER_STORIES.md
        ├── 02_ARCHITECTURE.md
        ├── 03_MIGRATION_GUIDE.md
        ├── 04_ROLLBACK_PLAN.md
        ├── 05_TEST_PLAN.md
        ├── 06_CI_WORKFLOW.md
        ├── 07_RELEASE_NOTES.md
        └── posters/
            └── phase16_architecture_poster.txt

server/
└── app/
    ├── api/
    │   └── routes/
    │       ├── video_submit.py
    │       ├── video_status.py
    │       └── video_results.py
    │
    ├── services/
    │   ├── storage/
    │   │   ├── base.py
    │   │   └── local_storage.py
    │   │
    │   ├── queue/
    │   │   ├── base.py
    │   │   └── in_memory_queue.py
    │   │
    │   └── worker/
    │       ├── worker_loop.py
    │       └── worker_runner.py
    │
    ├── models/
    │   └── job.py
    │
    ├── migrations/
    │   └── 000X_create_job_table.py
    │
    └── tests/
        └── video_jobs/
            ├── test_submit_job.py
            ├── test_job_status.py
            ├── test_job_results.py
            ├── test_worker_state_transitions.py
            ├── test_worker_pipeline_execution.py
            ├── fixtures/
            │   ├── tiny.mp4
            │   ├── make_tiny_mp4.py
            │   └── make_corrupt_mp4.py
            └── conftest.py
```

This structure enforces:

- **Separation of concerns**  
- **Governance boundaries**  
- **Test isolation**  
- **Deterministic behavior**  

---