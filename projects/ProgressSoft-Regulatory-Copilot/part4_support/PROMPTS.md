# Part 4: AI tool prompts

Five prompts for the owner of `part4_support/` to give, one at a time, to their own AI coding tool (Claude Code, Cursor, Copilot, ChatGPT, …). Open the tool **inside the repository folder** `AI-Topics-Course-Project` so it can read every file.

**How to use them**

- Give Prompt 1 first, in a new chat. It makes the tool study the whole project before it touches anything.
- Give the next prompt only after the previous pull request is merged (or at least pushed and reviewed).
- For every later prompt, start a fresh chat and paste the short **Start of every session** text first, then the prompt.
- Read and understand every line the tool writes. You present and defend this code.

## Start of every session (paste before Prompts 2–5)

```
You are my coding assistant for Part 4 (Support Agent and Orchestrator, Workflow B) of a 5-person student project.
Before doing anything: go to projects/ProgressSoft-Regulatory-Copilot/, run `git checkout main` and
`git pull`, list the folder tree, then read README.md, docs/source/00-Project-Guide.md, docs/source/04-Part4-Support-Agent-and-Orchestrator.md,
contracts/schemas.py and part4_support/PROMPTS.md. Follow the "Rules for the AI tool" in that file.
Then check what already exists in my folder and in the other part folders that I depend on,
summarise it in 5 lines, and wait for the task.
```

## Rules for the AI tool (it reads these every time)

1. **Where to work.** The Git repository is `AI-Topics-Course-Project`. The project lives in
   `projects/ProgressSoft-Regulatory-Copilot/`. Run every command from that folder.
2. **Your folder.** Edit only `part4_support/` (shared with Part 5: `tests/integration/`). Never edit another part's folder, `docs/`, or
   `contracts/schemas.py` (except the Contract Day prompt, and then only this part's own section).
   If something outside this folder needs to change, stop and write me a short GitHub Issue text instead.
3. **Other parts.** Use other parts only through their public functions in the Project Guide,
   Section 8.2. If a function does not exist yet, use its stub, or a small fake inside this part's tests.
4. **Read before writing.** The guides are Markdown files you can read:
   `docs/source/00-Project-Guide.md` and `docs/source/04-Part4-Support-Agent-and-Orchestrator.md`. Follow them exactly.
5. **Stack.** Python 3.11+, Pydantic v2, pytest. Follow the contracts in `contracts/schemas.py`.
   No new library without asking me; if I agree, add it to `requirements.txt`.
6. **Plan first.** Before writing code, show me a short plan (files, functions, tests) and wait for my "go".
7. **Small and tested.** Small functions with short comments. Every public function gets pytest tests in
   `part4_support/tests/`. Run `pytest part4_support/tests` and show me the result before committing.
8. **Git.** Never commit to `main` and never force-push. Start each task from an up-to-date `main`:
   `git checkout main`, `git pull`, then `git checkout -b <branch name from the prompt>`.
   Commit messages look like `feat(part4): ...`, `test(part4): ...` or `fix(part4): ...`.
   When done, `git push -u origin <branch>` and give me a pull request title and description that
   fills `.github/pull_request_template.md` (or open it with `gh pr create` if `gh` is installed).
9. **Safety.** Never put API keys or secrets in code or commits. `.env` is never committed.
   All data is fictional (Project Guide, Section 9).
10. **Log.** Add one line to `part4_support/AI_LOG.md` for this task (date, tool, short prompt, what we kept or changed).
11. **Finish with a report:** files changed, how to test, what is left, and any questions or Issues for teammates.

## Prompt 1 – Study the whole project, then the Contract Day work

```
You are my coding assistant for Part 4 (Support Agent and Orchestrator, Workflow B) of a 5-person student project, the
"Regulatory & Support Copilot". All five students work in the same GitHub repository, each in their
own part folder, each with their own AI tool.

Step 1 – Understand the whole project before doing anything:
- Make sure you are in `projects/ProgressSoft-Regulatory-Copilot/` and run `git checkout main` and `git pull`.
- List the whole folder tree (all folders and files, except .git and .venv) and tell me what each
  top-level folder is for and who owns it.
- Read `README.md`, `docs/source/00-Project-Guide.md` (all of it), `docs/source/04-Part4-Support-Agent-and-Orchestrator.md` (all of it),
  `contracts/schemas.py`, `contracts/CONTRACTS.md`, the repository's `../../.github/CODEOWNERS`,
  and the README of every part folder.
- Skim the other four part guides in `docs/source/` so you know what my teammates build and what they
  expect from me.
- Read `part4_support/PROMPTS.md` and follow its "Rules for the AI tool" in everything you do.

Step 2 – Report back to me (no code yet):
- A 10-line summary of the project and of my part.
- What my part must deliver, who depends on it, and what it depends on (with function names).
- The files you plan to create in `part4_support/`, in the order the guide's week plan suggests.
- Anything unclear or contradictory in the guides.

Step 3 – Then do this first task on branch `part4/contracts`:
- Write my contract models `TriageResult`, `TaskStep`, `Task` in the Part 4 section of `contracts/schemas.py`,
  with field descriptions and realistic examples (the TriageResult example from Section 8.1 of the Project
  Guide). Add a test that every example validates.
- In your report, list the `outputs` keys from the guide's Section 6.3 so I can confirm them with the team.
```

## Prompt 2 – Stubs and the SQLite task store

```
New task for Part 4. Follow the rules in part4_support/PROMPTS.md.
Create the branch `part4/stubs-and-store` from an up-to-date main.
Read the guide Sections 6.1 and 6.4 again.
Task:
1. `part4_support/triage.py` with a `triage(ticket)` stub returning the TriageResult example.
2. `part4_support/orchestrator/` with every public function from Section 6.1 as stubs (a fake finished
   task), re-exported in `orchestrator/__init__.py`, so Part 5 can build pages today.
3. Real `orchestrator/store.py`: SQLite at `settings.app_db`, table `tasks`, `save_task`, `load_task`,
   `query_tasks(type, status)` newest first, a new connection in every function, `with conn:` for writes.
4. Tests for the store (round trip, filters, ordering) using a temporary database file.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 3 – The orchestrator and command-line runner

```
New task for Part 4. Follow the rules in part4_support/PROMPTS.md.
Create the branch `part4/orchestrator` from an up-to-date main.
Read the guide Sections 6.2, 6.3 and 6.5 again.
Task:
1. Implement `start_regulation_task` and `start_ticket_task`: create the Task with all steps waiting, save,
   audit `task_created` (use `part5_web.safety.audit.log_event` if it exists, else a no-op fallback), run the
   steps in a daemon thread, return the task_id at once.
2. Each step: running → call the agent (Part 3 functions or `triage`) → save output under its key as
   `model_dump(mode="json")` → done with timing → audit `step_done`. Exceptions mark the step and task failed
   with the message and audit `step_failed`. After the last step the task is `pending_review`.
3. `get_task`, `list_tasks`, `set_task_status`, `update_output`, `retry_task`, `run_regulation_sync`,
   `run_ticket_sync`.
4. `python -m part4_support.orchestrator.run --regulation REG-003 | --ticket TCK-0007 | --list`.
5. Tests: step status sequence, a failing fake agent marks the task failed, background start returns
   immediately.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 4 – The Support Triage agent

```
New task for Part 4. Follow the rules in part4_support/PROMPTS.md.
Create the branch `part4/triage` from an up-to-date main.
Read the guide Section 5 again and look at the tickets and logs in `part1_data/data/`.
Task: implement `triage(ticket) -> TriageResult`:
1. Reference: regex first (payment 7731, ref 7731, ref=7731, transfer #7731 ...), LLM fallback only if needed.
2. Question path for general questions (answer from product docs, reason_code null).
3. Logs via `part1_data.tools.log_search.search_logs`: no entries → escalate, low confidence; settled →
   explain it settled; RJCT → take the reason code from the log.
4. RAG: reason-code passages and similar past tickets as sources.
5. One LLM call for root_cause and draft_reply, with prompt rules in `prompts/triage.md` (polite, plain words,
   next steps, no internal names or full account numbers, signed "Support Team").
6. Confidence by code (high / medium / low) and escalation.
Tests with fake LLM and mocked tools: rejected, settled, missing reference, general question, and at least
6 reference-writing styles.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 5 – Integration, error handling and quality run

```
New task for Part 4. Follow the rules in part4_support/PROMPTS.md.
Create the branch `part4/integration` from an up-to-date main.
Read the guide Sections 7, 9 and 12 again, and the Project Guide Section 14.
Task:
1. With the fake provider, write `tests/integration/test_workflow_regulation.py` and
   `test_workflow_ticket.py`: each runs the whole chain through the orchestrator and checks the task ends
   in `pending_review` with all outputs. (This folder is shared with Part 5; tell me what they should review.)
2. Make failures readable: every failed step stores a clear message; `retry_task` starts a new task.
3. Write `part4_support/tests/quality_check.py` that runs all tickets against
   `part1_data/data/eval/ticket_eval.json` (reference, reason code, escalation, root-cause keywords, no full
   account numbers in replies, average time). Run it with the team's real model and show me the table.
4. Replace `part4_support/README.md` with a one-page README (triage steps, task lifecycle, how to use the CLI).
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```
