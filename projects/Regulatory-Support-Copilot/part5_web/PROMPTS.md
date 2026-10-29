# Part 5: AI tool prompts

Five prompts for the owner of `part5_web/` to give, one at a time, to their own AI coding tool (Claude Code, Cursor, Copilot, ChatGPT, …). Open the tool **inside the repository folder** `AI-Topics-Course-Project` so it can read every file.

**How to use them**

- Give Prompt 1 first, in a new chat. It makes the tool study the whole project before it touches anything.
- Give the next prompt only after the previous pull request is merged (or at least pushed and reviewed).
- For every later prompt, start a fresh chat and paste the short **Start of every session** text first, then the prompt.
- Read and understand every line the tool writes. You present and defend this code.

## Start of every session (paste before Prompts 2–5)

```
You are my coding assistant for Part 5 (Website, Safety and Evaluation) of a 5-person student project.
Before doing anything: go to projects/ProgressSoft-Regulatory-Copilot/, run `git checkout main` and
`git pull`, list the folder tree, then read README.md, docs/source/00-Project-Guide.md, docs/source/05-Part5-Website-Safety-and-Evaluation.md,
contracts/schemas.py and part5_web/PROMPTS.md. Follow the "Rules for the AI tool" in that file.
Then check what already exists in my folder and in the other part folders that I depend on,
summarise it in 5 lines, and wait for the task.
```

## Rules for the AI tool (it reads these every time)

1. **Where to work.** The Git repository is `AI-Topics-Course-Project`. The project lives in
   `projects/ProgressSoft-Regulatory-Copilot/`. Run every command from that folder.
2. **Your folder.** Edit only `part5_web/` (shared with Part 4: `tests/integration/`; also the project's root `README.md`). Never edit another part's folder, `docs/`, or
   `contracts/schemas.py` (except the Contract Day prompt, and then only this part's own section).
   If something outside this folder needs to change, stop and write me a short GitHub Issue text instead.
3. **Other parts.** Use other parts only through their public functions in the Project Guide,
   Section 8.2. If a function does not exist yet, use its stub, or a small fake inside this part's tests.
4. **Read before writing.** The guides are Markdown files you can read:
   `docs/source/00-Project-Guide.md` and `docs/source/05-Part5-Website-Safety-and-Evaluation.md`. Follow them exactly.
5. **Stack.** Python 3.11+, Pydantic v2, pytest. Follow the contracts in `contracts/schemas.py`.
   No new library without asking me; if I agree, add it to `requirements.txt`.
6. **Plan first.** Before writing code, show me a short plan (files, functions, tests) and wait for my "go".
7. **Small and tested.** Small functions with short comments. Every public function gets pytest tests in
   `part5_web/tests/`. Run `pytest part5_web/tests` and show me the result before committing.
8. **Git.** Never commit to `main` and never force-push. Start each task from an up-to-date `main`:
   `git checkout main`, `git pull`, then `git checkout -b <branch name from the prompt>`.
   Commit messages look like `feat(part5): ...`, `test(part5): ...` or `fix(part5): ...`.
   When done, `git push -u origin <branch>` and give me a pull request title and description that
   fills `.github/pull_request_template.md` (or open it with `gh pr create` if `gh` is installed).
9. **Safety.** Never put API keys or secrets in code or commits. `.env` is never committed.
   All data is fictional (Project Guide, Section 9).
10. **Log.** Add one line to `part5_web/AI_LOG.md` for this task (date, tool, short prompt, what we kept or changed).
11. **Finish with a report:** files changed, how to test, what is left, and any questions or Issues for teammates.

## Prompt 1 – Study the whole project, then the Contract Day work

```
You are my coding assistant for Part 5 (Website, Safety and Evaluation) of a 5-person student project, the
"Regulatory & Support Copilot". All five students work in the same GitHub repository, each in their
own part folder, each with their own AI tool.

Step 1 – Understand the whole project before doing anything:
- Make sure you are in `projects/ProgressSoft-Regulatory-Copilot/` and run `git checkout main` and `git pull`.
- List the whole folder tree (all folders and files, except .git and .venv) and tell me what each
  top-level folder is for and who owns it.
- Read `README.md`, `docs/source/00-Project-Guide.md` (all of it), `docs/source/05-Part5-Website-Safety-and-Evaluation.md` (all of it),
  `contracts/schemas.py`, `contracts/CONTRACTS.md`, the repository's `../../.github/CODEOWNERS`,
  and the README of every part folder.
- Skim the other four part guides in `docs/source/` so you know what my teammates build and what they
  expect from me.
- Read `part5_web/PROMPTS.md` and follow its "Rules for the AI tool" in everything you do.

Step 2 – Report back to me (no code yet):
- A 10-line summary of the project and of my part.
- What my part must deliver, who depends on it, and what it depends on (with function names).
- The files you plan to create in `part5_web/`, in the order the guide's week plan suggests.
- Anything unclear or contradictory in the guides.

Step 3 – Then do this first task on branch `part5/contracts-and-sketch`:
- Write my contract models `ReviewDecision` and `AuditEvent` in the Part 5 section of `contracts/schemas.py`,
  with field descriptions and realistic examples. Add a test that the examples validate.
- Write `part5_web/PAGES.md`: a simple text sketch of every page in the guide's Section 5.2 (what is shown,
  which buttons, which public function each uses) so the team can agree on it.
```

## Prompt 2 – Safety stubs and the website skeleton

```
New task for Part 5. Follow the rules in part5_web/PROMPTS.md.
Create the branch `part5/stubs-and-skeleton` from an up-to-date main.
Read the guide Sections 5.1, 5.2 and 6 again.
Task:
1. `part5_web/safety/masking.py` with a `mask(text)` stub (returns text unchanged) and
   `part5_web/safety/audit.py` with `log_event(...)` and `list_events(...)` stubs, so Parts 2 and 4 can call them.
2. `part5_web/app.py` (FastAPI) with Jinja2 templates in `part5_web/templates/`, one CSS file in
   `part5_web/static/`: base layout, navigation with all pages from Section 5.2, footer with LLM provider and
   "Prototype – mock data", reviewer picker (cookie), and the Dashboard listing tasks from
   `part4_support.orchestrator.list_tasks()` (stub data is fine).
3. `uvicorn part5_web.app:app --reload` must work. Tests with FastAPI TestClient: every page returns 200.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 3 – Real masking, audit and the Task page

```
New task for Part 5. Follow the rules in part5_web/PROMPTS.md.
Create the branch `part5/safety-and-task-page` from an up-to-date main.
Read the guide Sections 5.3, 5.4, 6.1 and 6.2 again.
Task:
1. Real `mask()` for IBANs, long account numbers, card numbers, emails and phone numbers as in the table of
   Section 6.1; never mask short payment refs or reason codes; at least 15 tests.
2. Real `audit.py`: tables `audit_events` and `review_decisions` in the same SQLite file, `log_event` never
   raises, `list_events`, `save_decision`, `list_decisions`.
3. The Task page `/tasks/{task_id}` with the live timeline (poll `GET /api/tasks/{id}` every 2 s, stop when not
   running), the regulation cards and the ticket card, sources shown next to each claim, error + Retry for
   failed tasks.
4. Review actions (Approve / Edit / Reject, comment required for reject) following the table in Section 5.4,
   including `create_change_request` on approval. Test that no CR exists in mock ticketing before approval.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 4 – Remaining pages, API validation and prompt-injection test

```
New task for Part 5. Follow the rules in part5_web/PROMPTS.md.
Create the branch `part5/pages-and-api` from an up-to-date main.
Read the guide Sections 5.2, 5.5 and 6.3 again.
Task:
1. Pages: New Regulation (dropdown + paste with `parse_regulation`), Tickets (Run triage), Change Requests,
   Audit Log (filter by task), Knowledge Search (query, doc-type filter, Rebuild index button).
2. The JSON API exactly as Section 5.5, validating input at the boundary (404 unknown IDs, 400 empty text,
   decision must be approve/edit/reject). TestClient tests for each rule.
3. `part5_web/safety/guidelines.md` with the five rules of Section 6.3.
4. `tests/integration/test_prompt_injection.py`: triage on TCK-0021 must not claim approval and must keep the
   reason code from the logs. (This folder is shared with Part 4; tell me what they should review.)
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 5 – Evaluation, report and README

```
New task for Part 5. Follow the rules in part5_web/PROMPTS.md.
Create the branch `part5/evaluation` from an up-to-date main.
Read the guide Sections 7, 8 and 9 again.
Task:
1. `python -m part5_web.evaluation.run_eval` with `--only` and `--limit`: loads the three eval files from
   `part1_data/data/eval/`, runs items through `run_regulation_sync` / `run_ticket_sync` and `search`, computes
   every metric in Section 7.2, writes `runtime/eval/report.json` and `docs/evaluation-report.md`.
   (Writing that one file in `docs/` is allowed for this task.)
2. The Evaluation page shows the latest report with date and model.
3. Run it once with the fake provider and show me the summary.
4. Update the project's root `README.md` so a stranger can run both demos in 10 minutes (Section 8), and
   replace `part5_web/README.md` with a one-page README.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```
