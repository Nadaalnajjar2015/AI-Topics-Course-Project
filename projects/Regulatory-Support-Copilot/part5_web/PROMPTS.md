# Part 5: AI tool prompts

Five prompts for the owner of `part5_web/` to give, one at a time, to their own AI coding tool (Claude Code, Cursor, Copilot, ChatGPT, …). Open the tool **inside the repository folder** `AI-Topics-Course-Project` so it can read every file.

**How to use them**

- Give Prompt 1 first, in a new chat. It makes the tool study the whole project before it touches anything.
- Give the next prompt only after the previous pull request is merged (or at least pushed and reviewed).
- For every later prompt, start a fresh chat and paste the short **Start of every session** text first, then the prompt.
- Read and understand every line the tool writes. You present and defend this code, and you lead the final live demo.

## Start of every session (paste before Prompts 2–5)

```
You are my coding assistant for Part 5 (Website, Safety and Evaluation) of a 5-person student project.
Before doing anything: go to projects/Regulatory-Support-Copilot/, run `git checkout main` and
`git pull`, list the folder tree, then read README.md, docs/source/00-Project-Guide.md, docs/source/05-Part5-Website-Safety-and-Evaluation.md,
contracts/schemas.py, both part1_templates/templates/*/template.yaml files (if they exist) and part5_web/PROMPTS.md.
Follow the "Rules for the AI tool" in that file.
Then check what already exists in my folder and in the other part folders that I depend on,
summarise it in 5 lines, and wait for the task.
```

## Rules for the AI tool (it reads these every time)

1. **Where to work.** The Git repository is `AI-Topics-Course-Project`. The project lives in
   `projects/Regulatory-Support-Copilot/`. Run every command from that folder.
2. **Your folder.** Edit only `part5_web/` (shared with Part 4: `tests/integration/`; also the project's `README.md`). Never edit another part's folder, `docs/`, or
   `contracts/schemas.py` (except the Contract Day prompt, and then only this part's own section).
   If something outside this folder needs to change, stop and write me a short GitHub Issue text instead.
3. **Other parts.** Use other parts only through their public functions in the Project Guide,
   Section 8.2. If a function does not exist yet, use its stub, or a small fake inside this part's tests.
4. **Read before writing.** The guides are Markdown files you can read:
   `docs/source/00-Project-Guide.md` and `docs/source/05-Part5-Website-Safety-and-Evaluation.md`. Follow them exactly.
5. **General product.** Every organization name and label on every page comes from the active template
   (`load_template(template_id)`), chosen with the template switcher. Never hard-code "Client bank", "Student",
   "Cedar" or "Northfield" in HTML or Python. Test every page with both templates (payments and university).
6. **Stack.** Python 3.11+, FastAPI, Jinja2 templates (in `part5_web/templates/`, these are HTML templates),
   plain JavaScript, one CSS file, pytest. No front-end framework. No new library without asking me; if I agree,
   add it to `requirements.txt`.
7. **Plan first.** Before writing code, show me a short plan (files, functions, tests) and wait for my "go".
8. **Small and tested.** Small functions with short comments. Every public function and page gets pytest tests in
   `part5_web/tests/`. Run `pytest part5_web/tests` and show me the result before committing.
9. **Git.** Never commit to `main` and never force-push. Start each task from an up-to-date `main`:
   `git checkout main`, `git pull`, then `git checkout -b <branch name from the prompt>`.
   Commit messages look like `feat(part5): ...`, `test(part5): ...` or `fix(part5): ...`.
   When done, `git push -u origin <branch>` and give me a pull request title and description that
   fills `.github/pull_request_template.md` (or open it with `gh pr create` if `gh` is installed).
10. **Safety and log.** Never put API keys or secrets in code or commits; `.env` is never committed; all data is fictional
    (Project Guide, Section 9). Validate all API input. Add one line to `part5_web/AI_LOG.md` for this task (date, tool, short prompt, what we kept or changed).
11. **Finish with a report:** files changed, how to test, what is left, and any questions or Issues for teammates.

## Prompt 1 – Study the whole project, then the Contract Day work

```
You are my coding assistant for Part 5 (Website, Safety and Evaluation) of a 5-person student project, the
"Regulatory & Support Copilot". It is a general product: any organization customizes it with a template, and we
build two templates: a payments software company like ProgressSoft (main) and a university (second). The final presentation is a live demo of my website to the
doctor and the students. All five students work in the same GitHub repository, each in their own part folder,
each with their own AI tool.

Step 1 – Understand the whole project before doing anything:
- Make sure you are in `projects/Regulatory-Support-Copilot/` and run `git checkout main` and `git pull`.
- List the whole folder tree (all folders and files, except .git and .venv) and tell me what each
  top-level folder is for and who owns it.
- Read `README.md`, `docs/source/00-Project-Guide.md` (all of it), `docs/source/05-Part5-Website-Safety-and-Evaluation.md` (all of it),
  `contracts/schemas.py`, `contracts/CONTRACTS.md`, the repository's `../../.github/CODEOWNERS`,
  the README of every part folder, and anything already inside `part1_templates/templates/`.
- Skim the other four part guides in `docs/source/` so you know what my teammates build and what they
  expect from me.
- Read `part5_web/PROMPTS.md` and follow its "Rules for the AI tool" in everything you do.

Step 2 – Report back to me (no code yet):
- A 10-line summary of the project, the template idea, and my part.
- What my part must deliver, who depends on it, and what it depends on (with function names).
- How the template switcher changes what each page shows.
- The files you plan to create in `part5_web/`, in the order the guide's week plan suggests.
- Anything unclear or contradictory in the guides.

Step 3 – Then do this first task on branch `part5/contracts-and-sketch`:
- Write my contract models `ReviewDecision` and `AuditEvent` (with `template_id`) in the Part 5 section of
  `contracts/schemas.py`, with a `Field(description=...)` on every field and realistic examples. Add a test in
  `part5_web/tests/` that the examples validate.
- Write `part5_web/PAGES.md`: a simple text sketch of every page in the guide's Section 5.2, including the
  template switcher in the navigation bar and the Setup page (what is shown, which buttons, which public
  function each uses, which template labels appear), so the team can agree on it.
```

## Prompt 2 – Safety stubs and the website skeleton with the template switcher

```
New task for Part 5. Follow the rules in part5_web/PROMPTS.md.
Create the branch `part5/stubs-and-skeleton` from an up-to-date main.
Read the guide Sections 5.1, 5.2 and 6 again.
Task:
1. `part5_web/safety/masking.py` with a `mask(text)` stub (returns text unchanged) and
   `part5_web/safety/audit.py` with `log_event(actor, action, task_id, details, template_id=None)` and
   `list_events(...)` stubs, so Parts 2 and 4 can call them.
2. `part5_web/app.py` (FastAPI) with Jinja2 templates in `part5_web/templates/` and one CSS file in
   `part5_web/static/`: base layout with the organization name from the active template, navigation with all
   pages from Section 5.2, a template switcher (list_templates(), remembered in a cookie, default ACTIVE_TEMPLATE),
   a reviewer picker with the template's reviewers, a footer with LLM provider and "Prototype – mock data",
   and the Dashboard listing tasks from `part4_request_desk.orchestrator.list_tasks(template_id=...)` (stub data is fine).
3. `uvicorn part5_web.app:app --reload` must work. Tests with FastAPI TestClient: every page returns 200 for
   both templates, and switching the template changes the organization name in the header.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 3 – Real masking, audit, the Task page and review actions

```
New task for Part 5. Follow the rules in part5_web/PROMPTS.md.
Create the branch `part5/safety-and-task-page` from an up-to-date main.
Read the guide Sections 5.3, 5.4, 6.1 and 6.2 again.
Task:
1. Real `mask()` for IBANs (JO71 CBJO 0010 0000 0000 0131 0003 02), long account numbers, card numbers,
   national IDs, phone numbers and emails, as in the table of Section 6.1; never mask person IDs (BANK-C, S-2291),
   items (payment 7731, SE301), request IDs or reason codes (AC04); at least 15 tests with examples from both templates.
2. Real `audit.py`: tables `audit_events` (with template_id) and `review_decisions` in the same SQLite file,
   `log_event` never raises, `list_events(task_id, template_id)`, `save_decision`, `list_decisions`.
3. The Task page `/tasks/{task_id}` with the live timeline (poll `GET /api/tasks/{id}` every 2 s, stop when not
   running, show each step's message), the Change Watch cards (summary with quotes, impact table, action items)
   and the Request Desk card (item, reason code, evidence records, sources, confidence, reply), all with
   template labels; sources next to each claim; error + Retry for failed tasks.
4. Review actions (Approve / Edit / Reject, comment required for reject) following the table in Section 5.4,
   including `create_action_item` and `set_request_status` on approval. Test that no action item exists in the
   action list before approval.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 4 – Remaining pages, Setup page, API validation and prompt-injection tests

```
New task for Part 5. Follow the rules in part5_web/PROMPTS.md.
Create the branch `part5/pages-and-api` from an up-to-date main.
Read the guide Sections 5.2, 5.5 and 6.3 again.
Task:
1. Pages: New Change (dropdown + paste with `parse_change`), Requests (Investigate button), Action Items,
   Audit Log (filter by task), Knowledge Search (query, doc-type filter), and the Setup page (organization,
   languages, labels, units, stakeholder groups, connector, item pattern, document and chunk counts, Rebuild
   index button). Every page uses the active template.
2. The JSON API exactly as Section 5.5 with template_id, validating input at the boundary (404 unknown template,
   change, request or task; 400 empty text; 400 request from another template; decision must be
   approve/edit/reject). TestClient tests for each rule.
3. `part5_web/safety/guidelines.md` with the five rules of Section 6.3.
4. `tests/integration/test_prompt_injection.py`: investigation of P-REQ-015 and U-REQ-010 must not obey the
   injected instruction and must keep the reason code from the records. (This folder is shared with Part 4;
   tell me what they should review.)
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 5 – Evaluation per template, report, README and demo script

```
New task for Part 5. Follow the rules in part5_web/PROMPTS.md.
Create the branch `part5/evaluation-and-demo` from an up-to-date main.
Read the guide Sections 7, 8 and 9 again.
Task:
1. `python -m part5_web.evaluation.run_eval --template payments|university|all` with `--only` and `--limit`:
   loads each template's eval files from `part1_templates/templates/<id>/eval/`, runs items through
   `run_change_sync` / `run_request_sync` and `search`, computes every metric in Section 7.2 per template,
   writes `runtime/eval/report.json` and `docs/evaluation-report.md`. (Writing `docs/evaluation-report.md` and
   `docs/demo-script.md` is allowed for this task.)
2. The Evaluation page shows the latest report with date, model and one table per template.
3. Run it once with the fake provider for both templates and show me the summary.
4. Write `docs/demo-script.md` with Demos A, B and C from Section 8.2 (Demo A payments CHG-P-002, Demo B
   payments P-REQ-007, Demo C switch to university U-REQ-007 + Setup; timed, about 10 minutes), update the
   project `README.md` so a stranger can run all three demos in 10 minutes, and replace `part5_web/README.md`
   with a one-page README.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```
