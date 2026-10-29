# Part 1: Templates, Mock Data and Connectors

**Owner:** Zain Allateef - zaynallateef
**Guide:** `docs/01-Part1-Templates-Data-and-Connectors.pdf`
**AI tool prompts:** `PROMPTS.md` in this folder

The two organization templates (payments company like ProgressSoft, and university) with all their mock data, the record connectors, and the read-only tools every agent uses.

```
part1_templates/
templates/payments/    – main template: payments software company (like ProgressSoft)
templates/university/  – second template, same layout, smaller data set
connectors/            – base.py, transaction_lookup.py, registration_lookup.py
tools/                 – templates.py, changes.py, directory.py, requests.py, records.py, action_list.py
tests/
```

Only the owner edits this folder. Other parts use it only through the public functions listed in
`docs/00-Project-Guide.pdf`, Section 8.2. Replace this file with your own one-page README
(what the part does, inputs and outputs, how to run and test it).
