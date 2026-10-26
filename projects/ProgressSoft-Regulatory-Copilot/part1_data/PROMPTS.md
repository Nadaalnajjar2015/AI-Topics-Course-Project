# Part 1: AI tool prompts

Five prompts for the owner of `part1_data/` to give, one at a time, to their own AI coding tool (Claude Code, Cursor, Copilot, ChatGPT, …). Open the tool **inside the repository folder** `AI-Topics-Course-Project` so it can read every file.

**How to use them**

- Give Prompt 1 first, in a new chat. It makes the tool study the whole project before it touches anything.
- Give the next prompt only after the previous pull request is merged (or at least pushed and reviewed).
- For every later prompt, start a fresh chat and paste the short **Start of every session** text first, then the prompt.
- Read and understand every line the tool writes. You present and defend this code.

## Start of every session (paste before Prompts 2–5)

```
You are my coding assistant for Part 1 (Mock Data and Tools) of a 5-person student project.
Before doing anything: go to projects/ProgressSoft-Regulatory-Copilot/, run `git checkout main` and
`git pull`, list the folder tree, then read README.md, docs/source/00-Project-Guide.md, docs/source/01-Part1-Mock-Data-and-Tools.md,
contracts/schemas.py and part1_data/PROMPTS.md. Follow the "Rules for the AI tool" in that file.
Then check what already exists in my folder and in the other part folders that I depend on,
summarise it in 5 lines, and wait for the task.
```

## Rules for the AI tool (it reads these every time)

1. **Where to work.** The Git repository is `AI-Topics-Course-Project`. The project lives in
   `projects/ProgressSoft-Regulatory-Copilot/`. Run every command from that folder.
2. **Your folder.** Edit only `part1_data/`. Never edit another part's folder, `docs/`, or
   `contracts/schemas.py` (except the Contract Day prompt, and then only this part's own section).
   If something outside this folder needs to change, stop and write me a short GitHub Issue text instead.
3. **Other parts.** Use other parts only through their public functions in the Project Guide,
   Section 8.2. If a function does not exist yet, use its stub, or a small fake inside this part's tests.
4. **Read before writing.** The guides are Markdown files you can read:
   `docs/source/00-Project-Guide.md` and `docs/source/01-Part1-Mock-Data-and-Tools.md`. Follow them exactly.
5. **Stack.** Python 3.11+, Pydantic v2, pytest. Follow the contracts in `contracts/schemas.py`.
   No new library without asking me; if I agree, add it to `requirements.txt`.
6. **Plan first.** Before writing code, show me a short plan (files, functions, tests) and wait for my "go".
7. **Small and tested.** Small functions with short comments. Every public function gets pytest tests in
   `part1_data/tests/`. Run `pytest part1_data/tests` and show me the result before committing.
8. **Git.** Never commit to `main` and never force-push. Start each task from an up-to-date `main`:
   `git checkout main`, `git pull`, then `git checkout -b <branch name from the prompt>`.
   Commit messages look like `feat(part1): ...`, `test(part1): ...` or `fix(part1): ...`.
   When done, `git push -u origin <branch>` and give me a pull request title and description that
   fills `.github/pull_request_template.md` (or open it with `gh pr create` if `gh` is installed).
9. **Safety.** Never put API keys or secrets in code or commits. `.env` is never committed.
   All data is fictional (Project Guide, Section 9).
10. **Log.** Add one line to `part1_data/AI_LOG.md` for this task (date, tool, short prompt, what we kept or changed).
11. **Finish with a report:** files changed, how to test, what is left, and any questions or Issues for teammates.

## Prompt 1 – Study the whole project, then the Contract Day work

```
You are my coding assistant for Part 1 (Mock Data and Tools) of a 5-person student project, the
"Regulatory & Support Copilot". All five students work in the same GitHub repository, each in their
own part folder, each with their own AI tool.

Step 1 – Understand the whole project before doing anything:
- Make sure you are in `projects/ProgressSoft-Regulatory-Copilot/` and run `git checkout main` and `git pull`.
- List the whole folder tree (all folders and files, except .git and .venv) and tell me what each
  top-level folder is for and who owns it.
- Read `README.md`, `docs/source/00-Project-Guide.md` (all of it), `docs/source/01-Part1-Mock-Data-and-Tools.md` (all of it),
  `contracts/schemas.py`, `contracts/CONTRACTS.md`, the repository's `../../.github/CODEOWNERS`,
  and the README of every part folder.
- Skim the other four part guides in `docs/source/` so you know what my teammates build and what they
  expect from me.
- Read `part1_data/PROMPTS.md` and follow its "Rules for the AI tool" in everything you do.

Step 2 – Report back to me (no code yet):
- A 10-line summary of the project and of my part.
- What my part must deliver, who depends on it, and what it depends on (with function names).
- The files you plan to create in `part1_data/`, in the order the guide's week plan suggests.
- Anything unclear or contradictory in the guides.

Step 3 – Then do this first task on branch `part1/world-and-contracts`:
- Write `part1_data/data/WORLD.md` exactly as the guide's Section 5 describes (modules, clients, reason codes),
  with the MOCK DATA marker at the top.
- Write my four contract models `RegulationDoc`, `Client`, `LogEntry`, `Ticket` in the Part 1 section of
  `contracts/schemas.py`, each field with `Field(description=...)` and one realistic example in
  `model_config["json_schema_extra"]`. Add a test that each example validates.
- Follow the rules: plan first, tests, commit, push, PR text. This PR is reviewed by the whole team (Contract Day).
```

## Prompt 2 – Tool stubs and first data sample

```
New task for Part 1. Follow the rules in part1_data/PROMPTS.md.
Create the branch `part1/stubs-and-sample` from an up-to-date main.
Read the guide again (Sections 4, 6 and 7) and the current `contracts/schemas.py`.
Task:
1. Create every tool module in `part1_data/tools/` (`regulations.py`, `log_search.py`, `client_config.py`,
   `iso_validator.py`, `ticketing.py`) with the exact function signatures from the guide. For now each
   function returns contract example data (stubs), so teammates can import them today.
2. Create a first data sample: 2 product docs (ACH.md, IPS.md), `reason_codes.md`, 2 clients with configs,
   1 circular (REG-003), 5 tickets, and a small hand-written `transactions.jsonl` (about 100 lines) in the
   folders the guide names. Every file starts with the MOCK DATA marker.
3. Tests that every stub returns valid contract objects.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 3 – Complete the fictional world

```
New task for Part 1. Follow the rules in part1_data/PROMPTS.md.
Create the branch `part1/full-data` from an up-to-date main.
Read the guide Section 6 again, then `part1_data/data/WORLD.md` and the existing sample files.
Task: complete all mock data:
1. All 5 product documents with the required `##` headings, and a complete `reason_codes.md` (all 12 codes).
2. All 5 clients in `clients.json` and `configs/BANK-A.json` ... `BANK-E.json`, deliberately different.
3. All 6 circulars REG-001 ... REG-006 with header blocks, 2–4 numbered requirements and one background
   sentence each, matching the table in Section 6.4.
4. History: `past_tickets.json` (10) and `past_change_requests.json` (5, in the ChangeRequest format).
Use only the IDs in WORLD.md and only fictional names. When done, go through the consistency checklist
(Section 6.8) item by item and show me the result.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 4 – Logs, tickets and the consistency test

```
New task for Part 1. Follow the rules in part1_data/PROMPTS.md.
Create the branch `part1/logs-and-tickets` from an up-to-date main.
Read the guide Sections 6.5, 6.6 and 6.8 again.
Task:
1. Write `part1_data/data/generators/generate_logs.py` with `random.seed(42)`: about 600 LogEntry lines over
   3 days for all 5 clients, about 15% rejected across the reason codes, plus a clearly listed set of
   planted payments (fixed refs, clients and reason codes) used by the tickets. Some details contain
   fake IBANs for masking tests. Run it and commit the generated `transactions.jsonl`.
2. Write `tickets.json` with TCK-0001 ... TCK-0021 exactly as Section 6.6 describes (including the 2
   missing-reference tickets, 2 general questions and the prompt-injection ticket TCK-0021).
3. Write `part1_data/tests/test_data_consistency.py` that checks: every ticket reference exists in the logs
   (except the planned missing ones), every reason code in the logs is in reason_codes.md, and every
   expected client in the circulars has the right module and country.
4. Run the generator twice and prove the output is identical.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 5 – Real tools, evaluation sets and README

```
New task for Part 1. Follow the rules in part1_data/PROMPTS.md.
Create the branch `part1/tools-and-eval` from an up-to-date main.
Read the guide Sections 7, 8 and 10 again.
Task:
1. Replace the stubs with real implementations that read from DATA_DIR (default `part1_data/data`):
   `list_regulations`, `get_regulation`, `parse_regulation`, `search_logs` (all filters combinable, sorted,
   max 200), `list_clients`, `get_client`, `clients_with_module`, `validate_message`, and the ticketing
   functions. Ticket status changes and created change requests are saved only in
   `runtime/ticketing/state.json`; data files are never modified. Unknown IDs raise a clear KeyError.
2. Tests for every function, including unknown IDs and combined filters.
3. Write `part1_data/data/eval/regulation_eval.json`, `ticket_eval.json` and `search_eval.json` in the
   formats of Section 8, consistent with the data.
4. Replace `part1_data/README.md` with a one-page README (what the part does, file list, one usage
   example per tool, how to regenerate logs, how to run tests).
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```
