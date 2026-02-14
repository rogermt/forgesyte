
# ⭐ **PHASE‑16 FOLDER STRUCTURE**  
### *Authoritative directory layout for the entire phase*

```
server/
└── app/
    ├── api/
    │   └── routes/
    │       ├── job_submit.py
    │       ├── job_status.py
    │       └── job_results.py
    │
    ├── models/
    │   └── job.py
    │
    ├── migrations/
    │   └── versions/
    │       └── <timestamp>_create_job_table.py
    │
    ├── services/
    │   ├── storage/
    │   │   ├── base.py
    │   │   └── local_storage.py
    │   │
    │   ├── queue/
    │   │   ├── base.py
    │   │   └── memory_queue.py
    │   │
    │   └── workers/
    │       ├── worker.py
    │       └── worker_runner.py
    │
    └── services/
        └── video/
            └── video_file_pipeline_service.py   # Phase‑15 pipeline

tests/
└── app/
    ├── models/
    │   └── test_job.py
    ├── services/
    │   ├── storage/test_local_storage.py
    │   └── queue/test_memory_queue.py
    ├── workers/
    │   ├── test_job_worker.py
    │   └── test_worker_pipeline.py
    ├── api/
    │   ├── test_job_submit.py
    │   ├── test_job_status.py
    │   └── test_job_results.py
    └── fixtures/
        ├── tiny.mp4
        ├── make_tiny_mp4.py
        └── make_corrupt_mp4.py

.ampcode/
└── 04_PHASE_NOTES/
    └── Phase_16/
        ├── OVERVIEW.md
        ├── ARCHITECTURE.md
        ├── ENDPOINTS.md
        ├── MIGRATION_GUIDE.md
        ├── ROLLBACK_PLAN.md
        ├── CONTRIBUTOR_EXAM.md
        ├── RELEASE_NOTES.md
        └── posters/
            └── phase16_architecture_poster.txt

.github/
└── workflows/
    └── phase16_validation.yml

server/tools/
└── validate_phase16_path.py

server/tools/
└── forbidden_vocabulary_phase16.yaml

```

This structure enforces:

- **Separation of concerns**  
- **Governance boundaries**  
- **Test isolation**  
- **Deterministic behavior**  

---