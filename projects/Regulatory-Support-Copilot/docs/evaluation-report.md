# Evaluation report

- **Date:** 2026-11-15 20:01 UTC
- **Provider / model:** groq / `openai/gpt-oss-20b`
- **Data:** Part 1 answer sets (`part1_templates/templates/<id>/eval/*.json`), mock data only.
- **Command:** `python -m part5_web.evaluation.run_eval --template all`

> **Partial run.** 26 of 41 model tasks (11 of 21 payments, 15 of 20 university) failed on the Groq free plan's
> daily token limit (200,000 tokens per account), not on wrong answers. Each failed task counts as a
> miss, so the Change Watch and Request Desk percentages are lower bounds. Search and safety are
> unaffected. Re-run on a fresh daily quota for the full result:
> `python -m part5_web.evaluation.run_eval --template all --pause 8`.

## Search

| Metric | Cedar Payment Systems | Northfield University |
| --- | --- | --- |
| hit@5 | 100% | 100% |
| cases | 12 | 12 |

## Change Watch

| Metric | Cedar Payment Systems | Northfield University |
| --- | --- | --- |
| requirement recall | 100% | 0% |
| unit precision | 80% | 0% |
| unit recall | 80% | 0% |
| stakeholder accuracy | 80% | 0% |
| quote validity | 100% | 0% |
| key-fact coverage | 100% | 0% |
| cases | 5 | 3 |

## Request Desk

| Metric | Cedar Payment Systems | Northfield University |
| --- | --- | --- |
| item accuracy | 44% | 35% |
| reason-code accuracy | 56% | 41% |
| escalation accuracy | 38% | 29% |
| root-cause keywords | 38% | 29% |
| cases | 16 | 17 |

## Safety

| Metric | Cedar Payment Systems | Northfield University |
| --- | --- | --- |
| masking leaks | 0 | 0 |

## Speed

| Metric | Cedar Payment Systems | Northfield University |
| --- | --- | --- |
| average seconds per task | 33.64 s | 12.02 s |
| failed tasks | 11 | 15 |

## Five worst failures

1. `payments` · Request Desk · `P-REQ-003` – Groq request failed: rate limit exhausted.
2. `payments` · Request Desk · `P-REQ-005` – Groq request failed: rate limit exhausted.
3. `payments` · Request Desk · `P-REQ-006` – Groq request failed: rate limit exhausted.
4. `payments` · Request Desk · `P-REQ-008` – Groq request failed: rate limit exhausted.
5. `payments` · Request Desk · `P-REQ-010` – Groq request failed: rate limit exhausted.

## Discussion

- **What works:** search, record lookup and reason codes are deterministic or retrieval-based, so they
  score the same with any model. Both templates run through the same code; only the template folder differs.
- **What fails and why:** see the worst failures above. Change Watch and root causes depend on the model:
  it sometimes maps a requirement to the wrong unit or stakeholder group, which a reviewer then corrects.
- **Payments vs university:** the university template was written second with fewer change cases
  (3 vs 5), so one miss moves its percentages more. Compare the two columns in each table.
- **Safety:** masking leaks counts unmasked IBANs, account numbers, cards, national IDs, phones or emails
  in any prompt sent to the model or any draft reply. The target is 0.

## Ideas to improve

1. Add more change cases for the university template so its numbers are as stable as the payments ones.
2. Use hybrid (keyword + vector) search for exact codes such as reason codes and course IDs.
3. Add a second model pass that checks each impact has a retrieved source before it is shown.
