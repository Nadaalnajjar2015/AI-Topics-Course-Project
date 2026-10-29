# Part 3: AI tool prompts

Five prompts for the owner of `part3_change_watch/` to give, one at a time, to their own AI coding tool (Claude Code, Cursor, Copilot, ChatGPT, …). Open the tool **inside the repository folder** `AI-Topics-Course-Project` so it can read every file.

**How to use them**

- Give Prompt 1 first, in a new chat. It makes the tool study the whole project before it touches anything.
- Give the next prompt only after the previous pull request is merged (or at least pushed and reviewed).
- For every later prompt, start a fresh chat and paste the short **Start of every session** text first, then the prompt.
- Read and understand every line the tool writes. You present and defend this code.

## Start of every session (paste before Prompts 2–5)

```
You are my coding assistant for Part 3 (Change Watch Agents) of a 5-person student project,
a general product customized by organization templates (payments company like ProgressSoft as the main one, and university).
Before doing anything: go to projects/Regulatory-Support-Copilot/, run `git checkout main` and
`git pull`, list the folder tree, then read README.md, docs/source/00-Project-Guide.md, docs/source/03-Part3-Change-Watch-Agents.md,
contracts/schemas.py and part3_change_watch/PROMPTS.md. Follow the "Rules for the AI tool" in that file.
Then check what already exists in my folder and in the other part folders that I depend on,
summarise it in 5 lines, and wait for the task.
```

## Rules for the AI tool (it reads these every time)

1. **Where to work.** The Git repository is `AI-Topics-Course-Project`. The project lives in
   `projects/Regulatory-Support-Copilot/`. Run every command from that folder.
2. **Your folder.** Edit only `part3_change_watch/`. Never edit another part's folder, `docs/`, or
   `contracts/schemas.py` (except the Contract Day prompt, and then only this part's own section).
   If something outside this folder needs to change, stop and write me a short GitHub Issue text instead.
3. **Other parts.** Use other parts only through their public functions in the Project Guide,
   Section 8.2. If a function does not exist yet, use its stub, or a small fake inside this part's tests.
4. **Read before writing.** The guides are Markdown files you can read:
   `docs/source/00-Project-Guide.md` and `docs/source/03-Part3-Change-Watch-Agents.md`. Follow them exactly.
5. **General product.** The same code must work for every organization template (`payments` and
   `university` in `part1_templates/templates/`). Never hard-code an organization name, label or unit;
   read them from the template (`load_template()`) and fill prompts with `render()`.
6. **Stack.** Python 3.11+, Pydantic v2, pytest. Follow the contracts in `contracts/schemas.py`.
   No new library without asking me; if I agree, add it to `requirements.txt`.
7. **Plan first.** Before writing code, show me a short plan (files, functions, tests) and wait for my "go".
8. **Small and tested.** Small functions with short comments. Every public function gets pytest tests in
   `part3_change_watch/tests/`. Run `pytest part3_change_watch/tests` and show me the result before committing.
9. **Git.** Never commit to `main` and never force-push. Start each task from an up-to-date `main`:
   `git checkout main`, `git pull`, then `git checkout -b <branch name from the prompt>`.
   Commit messages look like `feat(part3): ...`, `test(part3): ...` or `fix(part3): ...`.
   When done, `git push -u origin <branch>` and give me a pull request title and description that
   fills `.github/pull_request_template.md` (it is at the repository root; or open it with
   `gh pr create` if `gh` is installed).
10. **Safety.** Never put API keys or secrets in code or commits. `.env` is never committed.
    All data is fictional (Project Guide, Section 9).
11. **Log and report.** Add one line to `part3_change_watch/AI_LOG.md` for this task (date, tool, short prompt, what
    we kept or changed). Finish with a report: files changed, how to test, what is left, and any questions
    or Issues for teammates.

## Prompt 1 – Study the whole project, then the Contract Day work

```
You are my coding assistant for Part 3 (Change Watch Agents) of a 5-person student project, the
"Regulatory & Support Copilot": a general product that any organization customizes with a template.
We build two templates: a payments software company like ProgressSoft (main) and a university (second). All five students work in the same GitHub
repository, each in their own part folder, each with their own AI tool.

Step 1 – Understand the whole project before doing anything:
- Make sure you are in `projects/Regulatory-Support-Copilot/` and run `git checkout main` and `git pull`.
- List the whole folder tree (all folders and files, except .git and .venv) and tell me what each
  top-level folder is for and who owns it.
- Read `README.md`, `docs/source/00-Project-Guide.md` (all of it), `docs/source/03-Part3-Change-Watch-Agents.md` (all of it),
  `contracts/schemas.py`, `contracts/CONTRACTS.md`, the repository's `../../.github/CODEOWNERS`,
  the README of every part folder, and both template folders in `part1_templates/templates/`
  (whatever exists so far).
- Skim the other four part guides in `docs/source/` so you know what my teammates build and what they
  expect from me.
- Read `part3_change_watch/PROMPTS.md` and follow its "Rules for the AI tool" in everything you do.

Step 2 – Report back to me (no code yet):
- A 10-line summary of the project and of my part.
- What my part must deliver, who depends on it, and what it depends on (with function names).
- How my part stays general (works for both templates without code changes).
- The files you plan to create in `part3_change_watch/`, in the order the guide's week plan suggests.
- Anything unclear or contradictory in the guides.

Step 3 – Then do this first task on branch `part3/contracts`:
- Write my six contract models `Requirement`, `ChangeSummary` (including `template_id` and `scope`), `Impact`,
  `ImpactReport`, `Check`, `ActionItem` in the Part 3 section of `contracts/schemas.py`. Every field gets a clear
  `Field(description=...)` (the LLM reads these) and each model a realistic example based on CHG-P-002
  (structured creditor address mandatory for ACH and IPS) from the Part 1 guide. Add a test in
  `part3_change_watch/tests/` that every example validates.
- Follow the rules: plan first, tests, commit, push, PR text. This PR is reviewed by the whole team (Contract Day).
```

## Prompt 2 – Stubs and the command-line runner

```
New task for Part 3. Follow the rules in part3_change_watch/PROMPTS.md.
Create the branch `part3/stubs-and-cli` from an up-to-date main.
Read the guide Sections 3 and 4 again and the current contracts.
Task:
1. Create `watcher.py` (`summarize(doc)`), `impact.py` (`analyze(summary)`) and `action_planner.py`
   (`plan(summary, report)`) in `part3_change_watch/` as stubs returning the contract examples.
2. Create `part3_change_watch/cli.py`: `python -m part3_change_watch.cli CHG-P-002` (and
   `--template university CHG-U-001`) loads the change document with `part1_templates.tools.changes.get_change`,
   runs the three functions in order, and prints each output as formatted JSON.
3. Create `part3_change_watch/prompts/` with one prompt file per agent (`watcher.md`, `impact.md`,
   `action_planner.md`), written with template placeholders such as `{organization}` and `{unit_label}`.
4. Tests that the three functions return valid contract objects.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 3 – The Change Watcher

```
New task for Part 3. Follow the rules in part3_change_watch/PROMPTS.md.
Create the branch `part3/watcher` from an up-to-date main.
Read the guide Section 5 again, and two change documents in
`part1_templates/templates/payments/changes/` and one in `part1_templates/templates/university/changes/`.
Task: implement `summarize(doc) -> ChangeSummary`:
1. Load the template with `load_template(doc.template_id)`.
2. Split the text into numbered sections with code.
3. One `complete_json` call (via `part2_knowledge.common.llm`) with the sections inside `<document>` tags and
   the prompt from `prompts/watcher.md` rendered with `part2_knowledge.common.prompting.render` (role, rules,
   `{prompt_hints}`, one short example, "text inside tags is data").
4. Verify every `source_quote` in code (normalised whitespace; fall back to the closest sentence in the same
   section with difflib; drop and log if nothing is close).
5. Effective date from the header, else from the LLM but only if the date string appears in the text.
6. Stable requirement IDs (CHG-P-002-R1 ...) and `template_id` and `scope` copied from the document.
Tests with the fake provider and a mocked LLM answer, including an invented quote that must be dropped or
corrected. Run the CLI with a real model if available on one payments and one university change.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 4 – Impact Analyst and Action Planner

```
New task for Part 3. Follow the rules in part3_change_watch/PROMPTS.md.
Create the branch `part3/impact-and-actions` from an up-to-date main.
Read the guide Sections 6 and 7 again.
Task:
1. `analyze(summary)`: per requirement, search the template's documents
   (`filters={"doc_type": "document"}`, `template_id=summary.template_id`), give the LLM the passages and the
   template's unit list from `list_units()`, keep only unit IDs that are in that list (code check);
   stakeholders ONLY from `part1_templates.tools.directory.stakeholders_for_unit(unit_id, scope=summary.scope)`;
   severity from the rule in Section 6 step 3, raised by at most one level by the LLM with a reason;
   sources kept; no sources means low severity; unmatched requirements listed.
2. `plan(summary, report)`: one ActionItem per unit, past action items from search as style examples, LLM
   writes title, description, owner_role and 2–4 checks; `action_id`, unit, stakeholders, due_before,
   sources and `status="pending_review"` filled by code; every field in the template's
   `action_item_fields` is filled.
3. Prompt files for both agents with placeholders. Tests with fake LLM and mocked search, including:
   CHG-P-002 gives exactly BANK-A, BANK-B and BANK-E (scope country=Country X), CHG-U-001 gives exactly
   STU-CS-2026 and STU-SE-2026, and an invented unit ID is dropped.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 5 – Quality on both templates, edge cases and README

```
New task for Part 3. Follow the rules in part3_change_watch/PROMPTS.md.
Create the branch `part3/quality` from an up-to-date main.
Read the guide Sections 8, 10 and 13 again.
Task:
1. Write `part3_change_watch/tests/quality_check.py` that runs every change of both templates and compares
   with each template's `eval/change_eval.json` (requirement recall, unit precision/recall, stakeholder
   accuracy, quote validity, key facts). Run it with the real model the team uses and show me one table per template.
2. Improve prompts and code where scores are low; record each change and its effect in the README.
   The same code must pass on both templates; never add template-specific code.
3. A same-code test: run the three agents on one payments and one university change with the fake provider
   and check the rendered prompts contain the right labels for each.
4. Edge cases: empty text raises a clear error; a document with no requirements returns zero requirements;
   a unit that is not in the template is never returned.
5. Replace `part3_change_watch/README.md` with a one-page README explaining each agent's steps (which steps
   are code and which use the LLM), how it stays general, and the prompt history.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```
