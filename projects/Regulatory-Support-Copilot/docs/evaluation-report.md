# Evaluation report

- **Date:** 2026-11-15 17:55 UTC
- **Provider / model:** fake / `openai/gpt-oss-20b`
- **Data:** Part 1 answer sets (`part1_templates/templates/<id>/eval/*.json`), mock data only.
- **Command:** `python -m part5_web.evaluation.run_eval --template all`

> **Fake provider run.** This checks that the evaluation script and every workflow run end to end.
> The fake model returns fixed answers, so Change Watch and root-cause numbers are **not** accuracy
> results. Re-run with the demo model (for example `LLM_PROVIDER=groq`) for the real result.

## Search

| Metric | Cedar Payment Systems |
| --- | --- |
| hit@5 | 100% |
| cases | 1 |

## Change Watch

| Metric | Cedar Payment Systems |
| --- | --- |
| requirement recall | 0% |
| unit precision | 0% |
| unit recall | 0% |
| stakeholder accuracy | 0% |
| quote validity | 0% |
| key-fact coverage | 100% |
| cases | 1 |

## Request Desk

| Metric | Cedar Payment Systems |
| --- | --- |
| item accuracy | 100% |
| reason-code accuracy | 100% |
| escalation accuracy | 100% |
| root-cause keywords | 0% |
| cases | 1 |

## Safety

| Metric | Cedar Payment Systems |
| --- | --- |
| masking leaks | 0 |

## Speed

| Metric | Cedar Payment Systems |
| --- | --- |
| average seconds per task | 0.12 s |
| failed tasks | 0 |

## Five worst failures

1. `payments` · Change Watch · `CHG-P-001` – units [] vs ['ACH', 'IPS'], found 0 requirements
2. `payments` · Request Desk · `P-REQ-001` – got {'item': '8820', 'reason_code': 'AC01', 'escalate': False}, expected {'item': '8820', 'reason_code': 'AC01', 'escalate': False}

## Discussion

- **What works:** search, record lookup and reason codes are deterministic or retrieval-based, so they
  score the same with any model. Both templates run through the same code; only the template folder differs.
- **What fails and why:** see the worst failures above. Change Watch quality depends on the model: the fake
  provider extracts no requirements, so its unit and quote numbers stay at zero.
- **Payments vs university:** the university template was written second with fewer change cases
  (3 vs 5), so one miss moves its percentages more. Compare the two columns in each table.
- **Safety:** masking leaks counts unmasked IBANs, account numbers, cards, national IDs, phones or emails
  in any prompt sent to the model or any draft reply. The target is 0.

## Ideas to improve

1. Add more change cases for the university template so its numbers are as stable as the payments ones.
2. Use hybrid (keyword + vector) search for exact codes such as reason codes and course IDs.
3. Add a second model pass that checks each impact has a retrieved source before it is shown.
