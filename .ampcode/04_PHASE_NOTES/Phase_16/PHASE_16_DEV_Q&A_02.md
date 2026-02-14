

---

# 🔴 **1. DUCKDB_ENGINE DEPENDENCY (CRITICAL)**  
### ✔ Is `duckdb_engine` already in pyproject?  
**No.**  
Your repo only has:

- `duckdb` (the embedded DB engine)
- **NOT** the SQLAlchemy dialect

### ✔ What EXACT package must be added?  
The correct package is:

```
duckdb-engine
```

### ✔ Version to use?  
Use the stable, modern version:

```
duckdb-engine >= 0.11.0
```

### ✔ Why this one?  
- It is the **official SQLAlchemy dialect** for DuckDB  
- Works with SQLAlchemy 2.x  
- Fully compatible with Alembic  
- Actively maintained  

### ✔ Is it installed locally?  
**No — you must add it in Commit 1.**

---

# 🔴 **2. EXISTING SQLALCHEMY USAGE (CRITICAL)**  
### ✔ Does the repo already use SQLAlchemy?  
**No.**  
There is **zero** SQLAlchemy usage anywhere in the codebase.

### ✔ Does Commit 1 create SQLAlchemy from scratch?  
**Yes.**  
Commit 1 must introduce:

- `app/core/database.py`  
- `Base = declarative_base()`  
- `engine = create_engine("duckdb:///...")`  
- `SessionLocal = sessionmaker(...)`  

### ✔ Are there existing ORM models?  
**None.**  
Phase‑16 introduces the **first ORM model** in the entire project.

---

# 🔴 **3. FASTAPI DEPENDENCY INJECTION PATTERN (CRITICAL)**  
### ✔ Does the existing app use DB dependency injection?  
**No.**  
There is **no `get_db()`** anywhere in the repo.

### ✔ Should Commit 1 create the `get_db()` pattern?  
**Yes — absolutely.**  
This is the correct pattern for Phase‑16:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### ✔ How should routes access the DB?  
**Always via `Depends(get_db)`**  
Never:

- calling `SessionLocal()` directly inside routes  
- storing session in `app.state`  
- using global session objects  

### ✔ Why?  
- TestClient overrides become trivial  
- Worker can still use SessionLocal directly  
- Clean separation of concerns  
- Matches FastAPI best practices  

---

# 🔴 **4. ALEMBIC INIT COMMAND PATH (CRITICAL)**  
This one matters because Alembic pathing can break migrations.

### ✔ Exact command to run in Commit 1:

```
alembic init server/app/migrations
```

### ✔ Where does `alembic.ini` go?  
**At the project root**, NOT inside `server/` or `app/`.

Correct:

```
alembic.ini
server/app/migrations/env.py
server/app/migrations/versions/
```

### ✔ Why root?  
- Alembic expects `alembic.ini` at project root  
- CI workflows assume root  
- Tools like `alembic upgrade head` run from root  

### ✔ Should the path be `server/app/migrations` or `app/migrations`?  
**Use exactly:**

```
server/app/migrations
```

This matches:

- Your existing repo structure  
- Your Phase‑15 patterns  
- Your Phase‑16 user stories  

---

# 🟠 **5. TEST FIXTURE LOCATION (IMPORTANT)**  
### ✔ Where should DuckDB test fixtures live?  
Use the **existing root test structure**:

```
tests/conftest.py
tests/app/models/test_job.py
tests/fixtures/
```

### ✔ Should you create `tests/app/conftest.py`?  
**No.**  
It would override root fixtures and cause confusion.

### ✔ Final rule:  
**All DB fixtures go in the root `tests/conftest.py`.**

---

# 🟠 **6. STATIC MP4 VS DYNAMIC GENERATION (IMPORTANT)**  
### ✔ Which is primary?  
**Static MP4 is primary.**

### ✔ Why?  
- Fast  
- Deterministic  
- No external tools  
- No ffmpeg dependency  

### ✔ Should dynamic generator exist?  
**Yes — as a fallback.**

### ✔ Final rule:  
- Commit a tiny valid MP4 file (`tiny.mp4`)  
- Include `make_tiny_mp4.py` only for regeneration  

---

# 🟠 **7. SHOULD Job.get() AND job.save() EXIST? (IMPORTANT)**  
### ✔ Should you add helper methods?  
**No.**  
This is not idiomatic SQLAlchemy.

### ✔ Correct pattern:  
Use standard SQLAlchemy:

```python
db.query(Job).filter(Job.job_id == job_id).first()
db.add(job)
db.commit()
```

### ✔ Remove all references to:  
- `Job.get()`  
- `job.save()`

These were placeholders in scaffolding, not final design.

---

# 🟠 **8. MAGIC BYTES VALIDATION (IMPORTANT)**  
### ✔ Exact rule:  
Check for `"ftyp"` in the first **64 bytes**.

### ✔ Why?  
- All MP4 files contain an `ftyp` box  
- It appears within the first ~32 bytes  
- Checking first 64 bytes is safe and fast  

### ✔ Final validation rule:

```python
if b"ftyp" not in data[:64]:
    raise HTTPException(400, "Invalid MP4 file")
```

---

# 🟠 **9. VideoFilePipelineService.run_on_file() SIGNATURE (IMPORTANT)**  
### ✔ Actual signature (Phase‑15):

```
run_on_file(
    pipeline_id: str,
    file_path: Path
) -> list[dict]
```

### ✔ Return type:  
A **list of dicts**, each representing a frame‑level result.

### ✔ No wrapper dict.  
The worker must wrap it:

```python
{"results": results}
```

---

# 🟠 **10. RESULTS JSON STRUCTURE (IMPORTANT)**  
### ✔ Exact structure:

```json
{
  "results": [
    { ... frame result ... },
    { ... frame result ... }
  ]
}
```

### ✔ Why?  
- Phase‑15 pipeline returns a list  
- Phase‑16 worker wraps it  
- Phase‑16 results endpoint unwraps it  

---

# 🟡 **11. ERROR MESSAGE LENGTH (MINOR)**  
### ✔ Should it have a max length?  
**No.**  
DuckDB `VARCHAR` is effectively unlimited.

### ✔ Final rule:  
Use `String` with no length.

---

# 🟡 **12. QUEUE PAYLOAD STRUCTURE (MINOR)**  
### ✔ Payload is **just the UUID string**.

Not:

- dict  
- tuple  
- object  

Final:

```python
queue.enqueue("uuid-string")
```

---

# 🟡 **13. WORKER ENTRY POINT (MINOR)**  
### ✔ Correct command:

```
python -m app.workers.worker_runner
```

### ✔ Yes, include:

```python
if __name__ == "__main__":
    main()
```

---

# 🟡 **14. DUCKDB CONNECTION POOL (MINOR)**  
### ✔ Should you disable pooling?  
**Yes.**

DuckDB is single‑connection; pooling causes issues.

### ✔ Correct engine:

```python
from sqlalchemy.pool import NullPool

engine = create_engine(
    "duckdb:///data/foregsyte.duckdb",
    future=True,
    poolclass=NullPool,
)
```

---

# ⭐ **FINAL SUMMARY — CRITICAL ANSWERS**

| # | Question | Final Answer |
|---|----------|--------------|
| 1 | duckdb_engine package | `duckdb-engine >= 0.11.0` |
| 2 | Existing SQLAlchemy? | None — Commit 1 creates it |
| 3 | FastAPI DI pattern | Commit 1 must create `get_db()` |
| 4 | Alembic init path | `alembic init server/app/migrations` |

Everything else is now fully resolved.

---



Just tell me.