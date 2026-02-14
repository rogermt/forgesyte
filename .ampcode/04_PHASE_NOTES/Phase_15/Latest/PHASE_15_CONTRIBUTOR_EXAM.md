# ⭐ **PHASE‑15 CONTRIBUTOR EXAM**  
### *20 questions, all answerable directly from the acceptance criteria.*

This is the exam you give to a new contributor before they’re allowed to open a PR.

---

## **Section 1 — Governance (5 questions)**

1. Where are phase‑named files allowed?  
2. Name three forbidden concepts in Phase‑15.  
3. What two fields must the payload contain?  
4. What is the only allowed top‑level response key?  
5. What must the smoke test script run, in order?

---

## **Section 2 — Pipeline & Payload (3 questions)**

6. How many nodes must `yolo_ocr.json` contain, and what are they?  
7. What is the required edge in the pipeline?  
8. Why must `image_bytes` be raw JPEG bytes instead of base64?

---

## **Section 3 — Service Logic (4 questions)**

9. What exception must be raised if OpenCV cannot open the file?  
10. How does `frame_stride` affect processing?  
11. What does `max_frames` do?  
12. What must always happen in a `finally` block?

---

## **Section 4 — Router & API (3 questions)**

13. What content types are allowed for uploads?  
14. What status code is returned for a missing pipeline?  
15. What status code is returned for missing form fields?

---

## **Section 5 — Testing (5 questions)**

16. What must the schema regression test assert about top‑level keys?  
17. What must the schema regression test assert about item keys?  
18. What is the purpose of the golden snapshot?  
19. What must the stress test verify about frame indices?  
20. What must the fuzz test guarantee about malformed MP4s?

