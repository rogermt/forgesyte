# ⭐ **2. PHASE‑15 ADVANCED EXAM (MUCH HARDER)**  
### *30 questions — deep architecture, governance, and failure‑mode reasoning*

This exam is designed for **senior maintainers** who must understand not just *what* Phase‑15 does, but *why* it is governed the way it is.

---

## **Section A — Architecture & Design (10 questions)**

1. Explain why Phase‑15 must remain synchronous and stateless.  
2. Describe how the DAG pipeline is invoked per frame and why this design prevents cross‑frame leakage.  
3. Why is `cv2.VideoCapture` used instead of ffmpeg subprocesses?  
4. What failure modes can occur when reading MP4 files, and how does Phase‑15 mitigate them?  
5. Why must JPEG encoding be done via `cv2.imencode` instead of Python libraries like Pillow?  
6. Explain why the pipeline must be defined in JSON rather than Python.  
7. Why is the golden snapshot generated using the mock DAG instead of real YOLO/OCR?  
8. Describe the exact boundary between Phase‑15 and Phase‑16.  
9. Why is the response schema frozen?  
10. What architectural risks does the governance validator prevent?

---

## **Section B — Testing & Determinism (10 questions)**

11. Why must `tiny.mp4` be committed instead of generated at test time?  
12. Explain how stride and max_frames interact and why this must be tested combinatorially.  
13. Why must fuzz tests use deterministic seeds?  
14. What is the purpose of the 1000‑frame stress test?  
15. Why must corrupted MP4s use a deterministic fake header?  
16. Why must the router tests assert exact HTTP status codes?  
17. Why must the schema regression test assert *exact* key sets?  
18. Why must the golden snapshot test forbid real model output?  
19. Why must the smoke test run governance checks before pytest?  
20. Why must the router wiring test exist even if integration tests pass?

---

## **Section C — Governance & CI (10 questions)**

21. Why must forbidden vocabulary be stored in YAML instead of Python?  
22. Why must the path validator detect phase‑named files?  
23. Why must the CI workflow trigger only on changes to `server/**`, `scripts/**`, and `server/tools/**`?  
24. Why must the smoke test exit on the first failure?  
25. Why must the rollback plan explicitly remove OpenCV?  
26. Why must the rollback plan restore Phase‑14 compatibility?  
27. Why must the migration guide avoid mentioning job queues?  
28. Why must the onboarding guide avoid referencing streaming?  
29. Why must the architecture diagram exist in both `.txt` and `.mmd` formats?  
30. Why must the release notes list exact file paths?

If you want, I can also generate the **answer key**.

---

# ⭐ **3. PHASE‑15 REVIEWER CERTIFICATION EXAM**  
### *20 questions — ensures reviewers can enforce governance mechanically*

---

## **Section 1 — Governance Enforcement (8 questions)**

1. What is the first thing you check in a Phase‑15 PR?  
2. How do you detect forbidden vocabulary?  
3. What is the rule for phase‑named files?  
4. What is the rule for response schema?  
5. What is the rule for payload schema?  
6. What is the rule for temp file cleanup?  
7. What is the rule for corrupted MP4 handling?  
8. What is the rule for golden snapshot regeneration?

---

## **Section 2 — Test Coverage (6 questions)**

9. What must unit tests use instead of real plugins?  
10. What must integration tests assert for 422 errors?  
11. What must integration tests assert for 400 errors?  
12. What must integration tests assert for 404 errors?  
13. What must the stress test verify?  
14. What must the fuzz test guarantee?

---

## **Section 3 — CI & Tooling (6 questions)**

15. What four steps must the smoke test run?  
16. What must the CI workflow run before pytest?  
17. What must the path validator detect?  
18. What must the forbidden vocabulary validator detect?  
19. What must the reviewer check in `main.py`?  
20. What must the reviewer check in `yolo_ocr.json`?

---

If you want, I can now generate:

🔥 **Answer keys** for both exams  
🔥 A **Reviewer Certification Certificate**  
🔥 A **Phase‑15 Governance Badge**  
🔥 A **Phase‑15 Maintainer Handbook**  

Just tell me which one you want next.