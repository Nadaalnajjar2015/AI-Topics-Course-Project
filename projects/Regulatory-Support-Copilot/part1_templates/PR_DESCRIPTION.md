## What this PR does

Builds Part 1 for the Regulatory & Support Copilot on `zainbranch`: six shared Part 1 contract models, complete payments and university mock datasets, deterministic record generators, read-only connectors, public tools, evaluation answer sets and documentation.

Payment 7731 resolves to BANK-C / ACH / REJECTED / AC04. S-2291's SE301 registration resolves to BLOCKED / PREREQ_MISSING with SE201 as the missing prerequisite. Scope filtering for CHG-P-002 returns BANK-A, BANK-B and BANK-E across ACH and IPS.

Runtime writes are atomic and isolated by template. Missing Part 2 settings and Part 3 action contracts are documented in `part1_templates/TEAM_ISSUES.md`; action-storage tests use a test-only fake. Real action creation needs Part 3's shared model. The JSON evaluation envelope also needs Part 5 agreement. Other part folders and contract sections are unchanged.

## Which part

- [x] Part 1
- [ ] Part 2
- [ ] Part 3
- [ ] Part 4
- [ ] Part 5

## How I tested it

From `projects/Regulatory-Support-Copilot/`:

```powershell
.\part1_templates\.venv\Scripts\python.exe -m pytest part1_templates/tests
.\part1_templates\.venv\Scripts\python.exe -m pytest part1_templates/tests/test_template_consistency.py -k generators -s
```

Tests cover the six contract examples, both YAML files and item patterns, all tools on both templates, all scope forms, unknown IDs/templates, connector filters and bounds, the 200-result cap, isolated writes, concurrent status updates and the consistency checklist. Both generators are run twice and matched byte-for-byte against committed JSONL. Final execution results are recorded in `part1_templates/REVIEW.md`.

## Screenshots (for website changes)

Not applicable; this PR changes Part 1 data and Python tools.

## Contract changes?

- [ ] No
- [x] Yes – all five members must approve

Schema changes are limited to the six Part 1 models and the user's editor-warning annotation on the existing Pydantic import. The user authorized the merge. No issue number is linked because draft issues have not been posted.
