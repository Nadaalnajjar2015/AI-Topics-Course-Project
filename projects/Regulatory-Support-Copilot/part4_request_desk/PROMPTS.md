# Part 4: AI tool prompts

Five prompts for the owner of `part4_request_desk/` to give, one at a time, to their own AI coding tool (Claude Code, Cursor, Copilot, ChatGPT, …). Open the tool **inside the repository folder** `AI-Topics-Course-Project` so it can read every file.

**How to use them**

- Give Prompt 1 first, in a new chat. It makes the tool study the whole project before it touches anything.
- Give the next prompt only after the previous pull request is merged (or at least pushed and reviewed).
- For every later prompt, start a fresh chat and paste the short **Start of every session** text first, then the prompt.
- Read and understand every line the tool writes. You present and defend this code.

## Start of every session (paste before Prompts 2–5)

```
You are my coding assistant for Part 4 (Request Desk Agent and Orchestrator) of a 5-person student project.
Before doing anything: go to projects/Regulatory-Support-Copilot/, run `git checkout main` and
`git pull`, list the folder tree, then read README.md, docs/source/00-Project-Guide.md, docs/source/04-Part4-Request-Desk-and-Orchestrator.md,
contracts/schemas.py, both part1_templates/templates/*/template.yaml files (if they exist) and part4_request_desk/PROMPTS.md.
Follow the "Rules for the AI tool" in that file.
Then check what already exists in my folder and in the other part folders that I depend on,
summarise it in 5 lines, and wait for the task.
```

## Rules for the AI tool (it reads these every time)

1. **Where to work.** The Git repository is `AI-Topics-Course-Project`. The project lives in
   `projects/Regulatory-Support-Copilot/`. Run every command from that folder.
2. **Your folder.** Edit only `part4_request_desk/` (shared with Part 5: `tests/integration/`). Never edit another part's folder, `docs/`, or
   `contracts/schemas.py` (except the Contract Day prompt, and then only this part's own section).
   If something outside this folder needs to change, stop and write me a short GitHub Issue text instead.
3. **Other parts.** Use other parts only through their public functions in the Project Guide,
   Section 8.2. If a function does not exist yet, use its stub, or a small fake inside this part's tests.
4. **Read before writing.** The guides are Markdown files you can read:
   `docs/source/00-Project-Guide.md` and `docs/source/04-Part4-Request-Desk-and-Orchestrator.md`. Follow them exactly.
5. **General product.** The same code must work for every template (payments and university). Never hard-code
   organization words such as bank, payment, student or course; read them from the template
   (`load_template()`: labels, item_pattern, reason_codes_doc, prompt_hints). Test both templates.
6. **Stack.** Python 3.11+, Pydantic v2, pytest, sqlite3 and threading from the standard library. Follow the contracts in
   `contracts/schemas.py`. No new library without asking me; if I agree, add it to `requirements.txt`.
7. **Plan first.** Before writing code, show me a short plan (files, functions, tests) and wait for my "go".
8. **Small and tested.** Small functions with short comments. Every public function gets pytest tests in
   `part4_request_desk/tests/`. Run `pytest part4_request_desk/tests` and show me the result before committing.
9. **Git.** Never commit to `main` and never force-push. Start each task from an up-to-date `main`:
   `git checkout main`, `git pull`, then `git checkout -b <branch name from the prompt>`.
   Commit messages look like `feat(part4): ...`, `test(part4): ...` or `fix(part4): ...`.
   When done, `git push -u origin <branch>` and give me a pull request title and description that
   fills `.github/pull_request_template.md` (or open it with `gh pr create` if `gh` is installed).
10. **Safety and log.** Never put API keys or secrets in code or commits; `.env` is never committed; all data is fictional
    (Project Guide, Section 9). Add one line to `part4_request_desk/AI_LOG.md` for this task (date, tool, short prompt, what we kept or changed).
11. **Finish with a report:** files changed, how to test, what is left, and any questions or Issues for teammates.

## Prompt 1 – Study the whole project, then the Contract Day work

```
You are my coding assistant for Part 4 (Request Desk Agent and Orchestrator) of a 5-person student project, the
"Regulatory & Support Copilot". It is a general product: any organization customizes it with a template, and we
build two templates: a payments software company like ProgressSoft (main) and a university (second). All five students work in the same GitHub repository, each in
their own part folder, each with their own AI tool.

Step 1 – Understand the whole project before doing anything:
- Make sure you are in `projects/Regulatory-Support-Copilot/` and run `git checkout main` and `git pull`.
- List the whole folder tree (all folders and files, except .git and .venv) and tell me what each
  top-level folder is for and who owns it.
- Read `README.md`, `docs/source/00-Project-Guide.md` (all of it), `docs/source/04-Part4-Request-Desk-and-Orchestrator.md` (all of it),
  `contracts/schemas.py`, `contracts/CONTRACTS.md`, the repository's `../../.github/CODEOWNERS`,
  the README of every part folder, and anything already inside `part1_templates/templates/`.
- Skim the other four part guides in `docs/source/` so you know what my teammates build and what they
  expect from me.
- Read `part4_request_desk/PROMPTS.md` and follow its "Rules for the AI tool" in everything you do.

Step 2 – Report back to me (no code yet):
- A 10-line summary of the project, the template idea, and my part.
- What my part must deliver, who depends on it, and what it depends on (with function names).
- How the payments and university templates differ for my Request Investigator (item, item_pattern, records, signature).
- The files you plan to create in `part4_request_desk/`, in the order the guide's week plan suggests.
- Anything unclear or contradictory in the guides.

Step 3 – Then do this first task on branch `part4/contracts`:
- Write my contract models `Investigation`, `TaskStep`, `Task` in the Part 4 section of `contracts/schemas.py`,
  with a `Field(description=...)` on every field and realistic examples: an Investigation for P-REQ-007
  (BANK-C, item 7731, reason AC04 closed account), and a Task that carries `template_id`. Add a test in
  `part4_request_desk/tests/` that every example validates.
- In your report, list the `outputs` keys from the guide's Section 6.3 so I can confirm them with the team.
```

## Prompt 2 – Stubs and the SQLite task store

```
New task for Part 4. Follow the rules in part4_request_desk/PROMPTS.md.
Create the branch `part4/stubs-and-store` from an up-to-date main.
Read the guide Sections 6.1 and 6.4 again.
Task:
1. `part4_request_desk/investigator.py` with an `investigate(request)` stub returning the Investigation example.
2. `part4_request_desk/orchestrator/` with every public function from Section 6.1 as stubs (a fake finished
   task), re-exported in `orchestrator/__init__.py`, so Part 5 can build pages today.
3. Real `orchestrator/store.py`: SQLite at `settings.app_db`, table `tasks` with a `template_id` column,
   `save_task`, `load_task`, `query_tasks(template_id, type, status)` newest first, a new connection in every
   function, `with conn:` for writes.
4. Tests for the store (round trip, filters including template_id, ordering) using a temporary database file.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 3 – The orchestrator and command-line runner

```
New task for Part 4. Follow the rules in part4_request_desk/PROMPTS.md.
Create the branch `part4/orchestrator` from an up-to-date main.
Read the guide Sections 6.2, 6.3 and 6.5 again.
Task:
1. Implement `start_change_task` and `start_request_task`: create the Task with the input's template_id and all
   steps waiting, save, audit `task_created` (use `part5_web.safety.audit.log_event` if it exists, else a no-op
   fallback), run the steps in a daemon thread, return the task_id at once.
2. Each step: running → call the agent (Part 3's summarize / analyze / plan, or `investigate`) → save the output
   under its key (summary, impact_report, action_items, investigation) as `model_dump(mode="json")` → done with
   timing → audit `step_done`. Exceptions mark the step and task failed with the message and audit `step_failed`.
   After the last step the task is `pending_review`.
3. `get_task`, `list_tasks(template_id, type, status)`, `set_task_status`, `update_output`, `retry_task`,
   `run_change_sync`, `run_request_sync`.
4. `python -m part4_request_desk.orchestrator.run --change CHG-P-002 | --request P-REQ-007 | --list`,
   with `--template university` to override ACTIVE_TEMPLATE (default payments).
5. Tests: step status sequence, a failing fake agent marks the task failed, background start returns
   immediately, tasks of the two templates stay separate in list_tasks.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 4 – The Request Investigator

```
New task for Part 4. Follow the rules in part4_request_desk/PROMPTS.md.
Create the branch `part4/investigator` from an up-to-date main.
Read the guide Section 5 again and look at the requests, records and template.yaml of BOTH templates in
`part1_templates/templates/`.
Task: implement `investigate(request) -> Investigation`, with everything organization-specific read from
`load_template(request.template_id)`:
1. Item: regex with the template's `item_pattern` first ("payment 7731" → group 1 = 7731 for payments, SE301 for the university),
   LLM fallback only if needed, checked against the same pattern.
2. Question path for general questions (answer from the template's documents, reason_code null).
3. Records via `part1_templates.tools.records.search_records(person_id, item, template_id)`. With no item:
   the person's records in the unit named in the text, latest failed record (with a reason code).
   No records (unknown reference) → escalate, low confidence; success (settled payment) → explain it succeeded;
   rejected/blocked → reason code from the record (e.g. search_records(person_id="BANK-C", item="7731") → AC04).
4. RAG: the reason-code section from the template's `reason_codes_doc` and similar past requests as sources.
5. One LLM call for root_cause and draft_reply; write `prompts/investigator.md` with placeholders
   ({organization}, {person_label}, {record_label}, {prompt_hints}) filled by `part2_knowledge.common.prompting.render`;
   polite, plain words, next steps, no full account numbers or other people's data, signed as the template's
   prompt_hints say ("Support Team, Cedar Payment Systems" / "Registrar's Office").
6. Confidence by code (high / medium / low) and escalation.
Tests with fake LLM and mocked tools for both templates: rejected/blocked, settled/success, unknown reference,
general question ("What is the cheque cut-off time?"),
person + unit fallback, and at least 6 item-writing styles per template. Show me the result for P-REQ-007
(AC04) and U-REQ-007 (PREREQ_MISSING).
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 5 – Integration, error handling and quality run

```
New task for Part 4. Follow the rules in part4_request_desk/PROMPTS.md.
Create the branch `part4/integration` from an up-to-date main.
Read the guide Sections 7, 9 and 12 again, and the Project Guide Section 14.
Task:
1. With the fake provider, write `tests/integration/test_workflow_change.py` and `test_workflow_request.py`:
   each runs the whole chain through the orchestrator for BOTH templates (parametrize over payments and
   university) and checks the task ends in `pending_review` with all outputs. (This folder is shared with Part 5;
   tell me what they should review.)
2. Make failures readable: every failed step stores a clear message; `retry_task` starts a new task.
3. Write `part4_request_desk/tests/quality_check.py` that runs all requests of each template against its
   `eval/request_eval.json` (item, reason code, escalation, root-cause keywords, no full account numbers or
   unmasked personal data in replies, average time). Run it with the team's real model and show me one table per template.
4. Replace `part4_request_desk/README.md` with a one-page README (investigator steps, how templates change
   its behaviour, task lifecycle, how to use the CLI).
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```
