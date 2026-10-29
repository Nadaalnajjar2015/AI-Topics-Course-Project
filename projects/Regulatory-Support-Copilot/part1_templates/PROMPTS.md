# Part 1: AI tool prompts

Five prompts for the owner of `part1_templates/` to give, one at a time, to their own AI coding tool (Claude Code, Cursor, Copilot, ChatGPT, …). Open the tool **inside the repository folder** `AI-Topics-Course-Project` so it can read every file.

**How to use them**

- Give Prompt 1 first, in a new chat. It makes the tool study the whole project before it touches anything.
- Give the next prompt only after the previous pull request is merged (or at least pushed and reviewed).
- For every later prompt, start a fresh chat and paste the short **Start of every session** text first, then the prompt.
- Read and understand every line the tool writes. You present and defend this code.

## Start of every session (paste before Prompts 2–5)

```
You are my coding assistant for Part 1 (Templates, Mock Data and Connectors) of a 5-person student project.
Before doing anything: go to projects/Regulatory-Support-Copilot/, run `git checkout main` and
`git pull`, list the folder tree, then read README.md, docs/source/00-Project-Guide.md,
docs/source/01-Part1-Templates-Data-and-Connectors.md, contracts/schemas.py and part1_templates/PROMPTS.md.
Follow the "Rules for the AI tool" in that file.
Then check what already exists in my folder and in the other part folders that I depend on,
summarise it in 5 lines, and wait for the task.
```

## Rules for the AI tool (it reads these every time)

1. **Where to work.** The Git repository is `AI-Topics-Course-Project`. The project lives in
   `projects/Regulatory-Support-Copilot/`. Run every command from that folder.
2. **Your folder.** Edit only `part1_templates/`. Never edit another part's folder, `docs/`, or
   `contracts/schemas.py` (except the Contract Day prompt, and then only this part's own section).
   If something outside this folder needs to change, stop and write me a short GitHub Issue text instead.
3. **Other parts.** Use other parts only through their public functions in the Project Guide,
   Section 8.2. If a function does not exist yet, use its stub, or a small fake inside this part's tests.
4. **Read before writing.** The guides are Markdown files you can read:
   `docs/source/00-Project-Guide.md` and `docs/source/01-Part1-Templates-Data-and-Connectors.md`. Follow them exactly.
5. **Stack.** Python 3.11+, Pydantic v2, pyyaml, pytest. Follow the contracts in `contracts/schemas.py`.
   No new library without asking me; if I agree, add it to `requirements.txt`.
   The product is general: never write organization-specific logic in tools; put differences in
   `template.yaml` or in a connector.
   All data is fictional (Cedar Payment Systems, BANK-A … BANK-E, Northfield University);
   ProgressSoft is only the real company that inspired the main template.
6. **Plan first.** Before writing code, show me a short plan (files, functions, tests) and wait for my "go".
7. **Small and tested.** Small functions with short comments. Every public function gets pytest tests in
   `part1_templates/tests/`. Run `pytest part1_templates/tests` and show me the result before committing.
8. **Git.** Never commit to `main` and never force-push. Start each task from an up-to-date `main`:
   `git checkout main`, `git pull`, then `git checkout -b <branch name from the prompt>`.
   Commit messages look like `feat(part1): ...`, `test(part1): ...` or `fix(part1): ...`.
   When done, `git push -u origin <branch>` and give me a pull request title and description that
   fills `.github/pull_request_template.md` (or open it with `gh pr create` if `gh` is installed).
9. **Safety.** Never put API keys or secrets in code or commits. `.env` is never committed.
   All data is fictional (Project Guide, Section 9).
10. **Log.** Add one line to `part1_templates/AI_LOG.md` for this task (date, tool, short prompt, what we kept or changed).
11. **Finish with a report:** files changed, how to test, what is left, and any questions or Issues for teammates.

## Prompt 1 – Study the whole project, then the Contract Day work

```
You are my coding assistant for Part 1 (Templates, Mock Data and Connectors) of a 5-person student
project, the "Regulatory & Support Copilot". It is a general product: one core engine that any
organization customizes with a template. We build two templates: the main one, "payments", a
payments software company like ProgressSoft (fictional name: Cedar Payment Systems), and a second
one, "university" (Northfield University). All five students work in the same GitHub repository,
each in their own part folder, each with their own AI tool.

Step 1 – Understand the whole project before doing anything:
- Make sure you are in `projects/Regulatory-Support-Copilot/` and run `git checkout main` and `git pull`.
- List the whole folder tree (all folders and files, except .git and .venv) and tell me what each
  top-level folder is for and who owns it.
- Read `README.md`, `docs/source/00-Project-Guide.md` (all of it),
  `docs/source/01-Part1-Templates-Data-and-Connectors.md` (all of it), `contracts/schemas.py`,
  `contracts/CONTRACTS.md`, the repository's `../../.github/CODEOWNERS`, and the README of every part folder.
- Skim the other four part guides in `docs/source/` so you know what my teammates build and what they
  expect from me.
- Read `part1_templates/PROMPTS.md` and follow its "Rules for the AI tool" in everything you do.

Step 2 – Report back to me (no code yet):
- A 10-line summary of the project and of my part.
- What my part must deliver, who depends on it, and what it depends on (with function names).
- The files you plan to create in `part1_templates/`, in the order the guide's week plan suggests.
- Anything unclear or contradictory in the guides.

Step 3 – Then do this first task on branch `part1/templates-and-contracts`:
- Write my six contract models `TemplateConfig`, `Unit`, `Stakeholder`, `ChangeDocument`, `Record`,
  `Request` in the Part 1 section of `contracts/schemas.py`, each field with `Field(description=...)`
  and one realistic example from the payments template in `model_config["json_schema_extra"]`
  (for example the planted record ref 7731, BANK-C, ACH, REJECTED, AC04).
- Write `part1_templates/templates/payments/template.yaml` and
  `part1_templates/templates/university/template.yaml` exactly as the guide's Section 5 describes.
- Add tests that every contract example validates, that both template.yaml files validate
  against `TemplateConfig`, and that each `item_pattern` finds "7731" in "Why was payment 7731
  rejected?" and "SE301" in "Why can't I register for SE301?".
- Follow the rules: plan first, tests, commit, push, PR text. This PR is reviewed by the whole team (Contract Day).
```

## Prompt 2 – Tool and connector stubs, first payments sample

```
New task for Part 1. Follow the rules in part1_templates/PROMPTS.md.
Create the branch `part1/stubs-and-sample` from an up-to-date main.
Read the guide again (Sections 4, 5, 6, 8 and 9) and the current `contracts/schemas.py`.
Task:
1. Create every tool module in `part1_templates/tools/` (`templates.py`, `changes.py`, `directory.py`,
   `requests.py`, `records.py`, `action_list.py`) with the exact function signatures from Section 9,
   each with an optional `template_id=None` (None = active template, default payments).
   `load_template` and `list_templates` read the real template.yaml files; every other function
   returns contract example data for now (stubs), so teammates can import them today.
2. Create `part1_templates/connectors/base.py` with the `RecordConnector` interface, stub
   `transaction_lookup.py` and `registration_lookup.py`, and the registry in `connectors/__init__.py`.
3. Create the first payments sample: `units.json` (5 modules), `stakeholders.json` (5 client banks),
   `documents/reason_codes.md`, `documents/ACH.md`, `documents/IPS.md`, `changes/CHG-P-002.md`,
   5 tickets in `requests/requests.json` (including P-REQ-007) and about 80 hand-written records in
   `records/transactions.jsonl` (including ref 7731 -> BANK-C -> ACH -> REJECTED -> AC04).
   Every file starts with the MOCK DATA marker.
4. Tests that every stub returns valid contract objects and that `load_template("university")` works.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 3 – Complete the payments template

```
New task for Part 1. Follow the rules in part1_templates/PROMPTS.md.
Create the branch `part1/payments-data` from an up-to-date main.
Read the guide Section 6 again, then the existing payments sample files.
Task: complete all payments data:
1. All 5 product modules and 5 client banks exactly as Sections 6.2 and 6.3 describe, with every
   attribute (country, message_standard, limits, cut-off times, local_rules).
2. All documents in Section 6.4: one product guide per module (CHQ, ACH, IPS, WAL, RPT) with the
   required `##` headings and real ISO 20022 element names, and `reason_codes.md` with one section
   per reason code (all 12).
3. All 5 circulars CHG-P-001 ... CHG-P-005 with header blocks (including `scope`, e.g.
   `country=Country X`), 2–4 numbered requirements and one background sentence each, matching the
   table in Section 6.5.
4. `generators/generate_records.py` with `random.seed(42)` (Section 6.6): about 500 transaction records
   over 3 days, only on modules each bank uses, the planted payments listed at the top of the script,
   fake IBANs or account numbers in some details. Run it and commit the generated `transactions.jsonl`.
5. All 15 tickets P-REQ-001 ... P-REQ-015 exactly as Section 6.7 describes (P-REQ-015 is the
   prompt-injection test), and the history files (6.8).
Use only the IDs in the guide and only fictional names. When done, go through the consistency checklist
(Section 11) item by item and show me the result.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 4 – University template and the consistency test

```
New task for Part 1. Follow the rules in part1_templates/PROMPTS.md.
Create the branch `part1/university-data` from an up-to-date main.
Read the guide Sections 7 and 11 again, and look at the finished payments template as the model.
Task:
1. Build the university template exactly as Section 7 describes: units, stakeholder groups, documents
   (with one section per reason code in `registration_rules.md` and SE301 with prerequisite SE201 in
   the SE-BSc study plan), CHG-U-001 ... CHG-U-003, the record generator `generators/generate_records.py`
   (seed 42, about 250 registration records, planted record S-2291 / SE301 / BLOCKED / PREREQ_MISSING),
   requests U-REQ-001 ... U-REQ-010 (U-REQ-010 is the prompt-injection test) and history.
2. Do not change any tool code for this: if you feel you must, tell me why first (the product must be general).
3. Write `part1_templates/tests/test_template_consistency.py`, parametrized over both templates, that checks
   the first five points of the checklist in Section 11.
4. Run both generators twice and prove the output is identical.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 5 – Real tools and connectors, evaluation sets and README

```
New task for Part 1. Follow the rules in part1_templates/PROMPTS.md.
Create the branch `part1/tools-and-eval` from an up-to-date main.
Read the guide Sections 8, 9, 10, 12 and 14 again.
Task:
1. Implement both connectors for real (`transaction_lookup`, `registration_lookup`; all filters
   combinable, newest first, max 200, read-only) and replace the tool stubs with real implementations:
   `list_changes`, `get_change`, `parse_change`, `list_units`, `get_unit`, `list_stakeholders`,
   `stakeholders_for_unit` (with every form of the scope rule from Section 5, including `key=value`),
   `list_requests`, `get_request`, `set_request_status`, `search_records` (calls the template's
   connector), `create_action_item`, `list_action_items`. Writes go only to
   `runtime/<template_id>/state.json`. Unknown IDs and unknown templates raise clear errors.
2. Tests for every function on both templates, including unknown IDs, combined filters and the scope rule
   (for example CHG-P-002's units ACH and IPS with scope `country=Country X` give BANK-A, BANK-B, BANK-E).
3. Write `eval/change_eval.json`, `request_eval.json` and `search_eval.json` for both templates in the
   formats of Section 10, consistent with the data (payments: 5, 15, 12; university: 3, 10, 8).
4. Replace `part1_templates/README.md` with a one-page README (what the part does, folder list, one usage
   example per tool, how to regenerate records, how to run tests) and write `templates/README.md`
   (the template format and "how to add a third template" from Section 12, with a hospital as the example).
   Keep the Owner line as it is.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```
