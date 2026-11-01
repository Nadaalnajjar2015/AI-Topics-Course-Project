# Part 1 data review — 2026-11-02

Part 1 satisfies the local deliverables in Guide 1. Its original 95 tests passed before changes. The university had enough rows for the planned small demonstration, but nursing lacked useful course and evaluation coverage. This review adds coverage while keeping the university smaller than the 500-record payments dataset.

All records, curricula, organizations and policies here are fictional. This review uses repository fixtures and the checked-in guide; it does not add external nursing or patient data.

## Coverage before and after

| Measure | Before | After |
| --- | ---: | ---: |
| University registration events | 250 | 300 |
| University distinct students | 50 | 60 |
| University knowledge documents | 7 | 8 |
| University requests / request evaluation cases | 10 / 10 | 17 / 17 |
| University search evaluation cases | 8 | 12 |
| University historical requests | 5 | 7 |
| Nursing registration events | 54 | 104 |
| Nursing distinct students | 11 | 21 |
| Nursing distinct courses in records | 2 | 8 |
| Nursing study-plan documents | 0 | 1 |
| Nursing record-backed request cases | 1 | 8 |
| Nursing evaluated failure reasons | 1 of 7 | 7 of 7 |
| Nursing evaluated success cases | 0 | 1 |
| Payments requests / request evaluation cases | 15 / 15 | 16 / 16 |
| Active question bodies copied into history, payments / university | 8 / 5 | 0 / 0 |

The existing demo records, request IDs and change IDs remain intact. The original 250 university rows retain their exact bytes, checked by their original SHA-256. The 50 added nursing rows cover 10 new students with five distinct courses per student; their background events do not reuse the planted request's student/course pair.

## Gaps addressed

1. **Missing nursing evidence.** `study_plan_NUR-BSc.md` documents eight courses, prerequisite relationships, advisor approvals, capacity, internship scope and attendance dates. NUR210 requires NUR101. Nursing is included in the attendance circular but excluded from the computing-only internship extension.
2. **Thin nursing request coverage.** U-REQ-011 through U-REQ-017 add missing prerequisite, full section, unpaid fees, timetable conflict, credit limit, late registration and success. Together with U-REQ-005's advisor hold, these cover every registration reason. Four additional retrieval questions target nursing evidence; two additional history examples cover prerequisites and late registration.
3. **Copied history/evaluation questions.** All 13 historical question bodies previously repeated active request bodies. They now describe separate historical situations. Historical resolutions still demonstrate the same policy concepts, which is intentional for this RAG prototype; this does not create an independent held-out benchmark.
4. **Unspecified payments cause not evaluated.** P-REQ-016 uses the existing BANK-D / RPT / 9200 / MS03 record and expects escalation for manual investigation. This tests a known record with no specific cause, alongside the two existing missing-record escalations. No payment records needed adding.
5. **Coverage gaps hidden by count-only tests.** The repeatable audit and new regressions check missing study plans, uncovered reason codes, request/evaluation alignment, copied historical questions and nursing breadth. Existing reproducibility, dates, scopes and connector tests still apply.

## Current distribution

| Program | Events | Students | Courses in records | Record-backed request cases |
| --- | ---: | ---: | ---: | ---: |
| CS-BSc | 70 | 14 | 3 | 2 |
| SE-BSc | 66 | 13 | 4 | 3 |
| BUS-BBA | 60 | 12 | 2 | 2 |
| NUR-BSc | 104 | 21 | 8 | 8 |

University outcomes: 238 registered, 50 blocked and 12 waitlisted. Nursing outcomes: 87 registered, 14 blocked and 3 waitlisted. The nursing supplement deliberately improves coverage rather than approximating a real population distribution.

Payments remains at 500 records across all five banks and five modules: ACH 142, IPS 142, WAL 89, CHQ 76 and RPT 51. It has 425 settled and 75 failed outcomes, preserving the guide's 15% failure target. Every one of its 12 reason codes is now represented in a request evaluation case.

## Part 1 deliverable audit

| Guide deliverable | Finding |
| --- | --- |
| D1: template format and both configurations | Present; both validate against TemplateConfig, including vocabulary and item patterns. |
| D2: payments units, banks, guides and circulars | Five modules, five banks, six knowledge documents and five circulars; memberships and scoped impact expectations pass. |
| D3: payments generator and records | Seed-42 generator reproduces all 500 records; 75 failures, three expected dates and fixed demo records verified. |
| D4: payments requests, history and evaluation | Now 16 requests, eight historical requests, four historical actions and 5 / 16 / 12 evaluation cases; the guide's original 15 tickets remain. |
| D5: university template | Now 300 records, 60 students, eight documents, three circulars, 17 requests, seven historical requests, two historical actions and 3 / 17 / 12 evaluation cases. |
| D6: connectors | Both adapters validate Records, combine filters, enforce inclusive dates, sort newest first, cap at 200 and leave source data unchanged. |
| D7: tools | Every public function is exercised for both templates, including lookup errors, scope forms and isolated runtime storage. Real action storage still needs Part 3's model. |
| D8: tests | 100 Part 1 tests pass, including the new coverage checks; both generators reproduce committed bytes twice. |
| D9: documentation and AI log | Updated counts, evaluation semantics, reproduction command, this review and remaining integration issues are documented. |
| D10: six shared Part 1 models | Present with field descriptions and validated examples; no contract edits were needed. |

## Remaining limits and integration work

- These are small, seeded synthetic fixtures for functional demonstrations. They do not establish real nursing outcomes, real-world error rates, model-training sufficiency or statistically reliable agent accuracy.
- The original university data contains 126 events beyond the first event for each student/course pair. They have different event IDs, and there are no exact duplicate rows. Treat them as event history, not 300 independent enrollments; the generator does not model a complete academic state or enforce a realistic progression between retries. Full transcript and course-credit state are outside this fixture.
- Other programs still have narrower course and per-program reason coverage. Every university reason is evaluated somewhere, and nursing covers all seven, but this is not an exhaustive program-by-reason test matrix. Office units have no course-registration records by design.
- Records span only one registration week for university and three days for payments. There is no semester-to-semester, seasonal, multilingual or independently authored holdout evaluation. Configured language support is not evidence of bilingual evaluation coverage.
- General-question answers use the request's scenario date. U-REQ-009 is from February 2026, so its 15% answer is consistent with the attendance change taking effect in September; it must not be treated as a timeless current-policy answer.
- Part 2 settings and ingestion, Part 3's real ActionItem/Check and related SearchResult contracts, and the Part 5 evaluation runner are still missing. Real RAG retrieval, generated replies, approval flows and safety performance have not been executed. Human teammate approval and acceptance of the evaluation envelope cannot be established by local tests. See [TEAM_ISSUES.md](TEAM_ISSUES.md).

## Reproduce

Run from `projects/Regulatory-Support-Copilot/` with the project's Python environment:

```powershell
python -m part1_templates.analyze_data
python -m pytest part1_templates/tests -q
python -m pytest part1_templates/tests/test_template_consistency.py -k generators -s
```

The audit reads the complete JSONL files directly. An unfiltered connector call returns only the newest 200 rows, so it cannot measure dataset size. The local verification used `part1_templates/.venv/Scripts/python.exe`: **100 tests passed**; both reproducibility cases passed separately.

| Generated file | SHA-256 |
| --- | --- |
| Payments | `879900e95a94227b57a6903df9fce2339bab9bbebb187ddde03f91ee4f59c831` |
| University, expanded | `58c40f858201647fdcd372936ec64bcd5faecac87977066ac6d7dba19e1963ea` |
| University, original 250 rows plus note | `46c7774bfd78393b0985fec2bb03ec1b6bfd7672415c82b4d6fcbcf241a1464c` |
