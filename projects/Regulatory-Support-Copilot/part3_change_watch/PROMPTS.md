# Part 3: AI tool prompts

Five prompts for the owner of `part3_regulation/` to give, one at a time, to their own AI coding tool (Claude Code, Cursor, Copilot, ChatGPT, …). Open the tool **inside the repository folder** `AI-Topics-Course-Project` so it can read every file.

**How to use them**

- Give Prompt 1 first, in a new chat. It makes the tool study the whole project before it touches anything.
- Give the next prompt only after the previous pull request is merged (or at least pushed and reviewed).
- For every later prompt, start a fresh chat and paste the short **Start of every session** text first, then the prompt.
- Read and understand every line the tool writes. You present and defend this code.

## Start of every session (paste before Prompts 2–5)

```
You are my coding assistant for Part 3 (Regulation Agents, Workflow A) of a 5-person student project.
Before doing anything: go to projects/ProgressSoft-Regulatory-Copilot/, run `git checkout main` and
`git pull`, list the folder tree, then read README.md, docs/source/00-Project-Guide.md, docs/source/03-Part3-Regulation-Agents.md,
contracts/schemas.py and part3_regulation/PROMPTS.md. Follow the "Rules for the AI tool" in that file.
Then check what already exists in my folder and in the other part folders that I depend on,
summarise it in 5 lines, and wait for the task.
```

## Rules for the AI tool (it reads these every time)

1. **Where to work.** The Git repository is `AI-Topics-Course-Project`. The project lives in
   `projects/ProgressSoft-Regulatory-Copilot/`. Run every command from that folder.
2. **Your folder.** Edit only `part3_regulation/`. Never edit another part's folder, `docs/`, or
   `contracts/schemas.py` (except the Contract Day prompt, and then only this part's own section).
   If something outside this folder needs to change, stop and write me a short GitHub Issue text instead.
3. **Other parts.** Use other parts only through their public functions in the Project Guide,
   Section 8.2. If a function does not exist yet, use its stub, or a small fake inside this part's tests.
4. **Read before writing.** The guides are Markdown files you can read:
   `docs/source/00-Project-Guide.md` and `docs/source/03-Part3-Regulation-Agents.md`. Follow them exactly.
5. **Stack.** Python 3.11+, Pydantic v2, pytest. Follow the contracts in `contracts/schemas.py`.
   No new library without asking me; if I agree, add it to `requirements.txt`.
6. **Plan first.** Before writing code, show me a short plan (files, functions, tests) and wait for my "go".
7. **Small and tested.** Small functions with short comments. Every public function gets pytest tests in
   `part3_regulation/tests/`. Run `pytest part3_regulation/tests` and show me the result before committing.
8. **Git.** Never commit to `main` and never force-push. Start each task from an up-to-date `main`:
   `git checkout main`, `git pull`, then `git checkout -b <branch name from the prompt>`.
   Commit messages look like `feat(part3): ...`, `test(part3): ...` or `fix(part3): ...`.
   When done, `git push -u origin <branch>` and give me a pull request title and description that
   fills `.github/pull_request_template.md` (or open it with `gh pr create` if `gh` is installed).
9. **Safety.** Never put API keys or secrets in code or commits. `.env` is never committed.
   All data is fictional (Project Guide, Section 9).
10. **Log.** Add one line to `part3_regulation/AI_LOG.md` for this task (date, tool, short prompt, what we kept or changed).
11. **Finish with a report:** files changed, how to test, what is left, and any questions or Issues for teammates.

## Prompt 1 – Study the whole project, then the Contract Day work

```
You are my coding assistant for Part 3 (Regulation Agents, Workflow A) of a 5-person student project, the
"Regulatory & Support Copilot". All five students work in the same GitHub repository, each in their
own part folder, each with their own AI tool.

Step 1 – Understand the whole project before doing anything:
- Make sure you are in `projects/ProgressSoft-Regulatory-Copilot/` and run `git checkout main` and `git pull`.
- List the whole folder tree (all folders and files, except .git and .venv) and tell me what each
  top-level folder is for and who owns it.
- Read `README.md`, `docs/source/00-Project-Guide.md` (all of it), `docs/source/03-Part3-Regulation-Agents.md` (all of it),
  `contracts/schemas.py`, `contracts/CONTRACTS.md`, the repository's `../../.github/CODEOWNERS`,
  and the README of every part folder.
- Skim the other four part guides in `docs/source/` so you know what my teammates build and what they
  expect from me.
- Read `part3_regulation/PROMPTS.md` and follow its "Rules for the AI tool" in everything you do.

Step 2 – Report back to me (no code yet):
- A 10-line summary of the project and of my part.
- What my part must deliver, who depends on it, and what it depends on (with function names).
- The files you plan to create in `part3_regulation/`, in the order the guide's week plan suggests.
- Anything unclear or contradictory in the guides.

Step 3 – Then do this first task on branch `part3/contracts`:
- Write my six contract models `Change`, `RegulationSummary` (including `country`), `Impact`, `ImpactReport`,
  `TestCase`, `ChangeRequest` in the Part 3 section of `contracts/schemas.py`. Every field gets a clear
  `Field(description=...)` (the LLM reads these) and each model a realistic example based on REG-003 from
  the Part 1 guide. Add a test that every example validates.
```

## Prompt 2 – Stubs and the command-line runner

```
New task for Part 3. Follow the rules in part3_regulation/PROMPTS.md.
Create the branch `part3/stubs-and-cli` from an up-to-date main.
Read the guide Sections 3 and 4 again and the current contracts.
Task:
1. Create `watcher.py` (`summarize(doc)`), `impact.py` (`analyze(summary)`) and `change_request.py`
   (`draft(summary, report)`) in `part3_regulation/` as stubs returning the contract examples.
2. Create `part3_regulation/cli.py`: `python -m part3_regulation.cli REG-003` loads the circular with
   `part1_data.tools.regulations.get_regulation`, runs the three functions in order, and prints each output
   as formatted JSON.
3. Create `part3_regulation/prompts/` with one empty prompt file per agent.
4. Tests that the three functions return valid contract objects.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 3 – The Regulation Watcher

```
New task for Part 3. Follow the rules in part3_regulation/PROMPTS.md.
Create the branch `part3/watcher` from an up-to-date main.
Read the guide Section 5 again, and two circulars in `part1_data/data/regulations/`.
Task: implement `summarize(doc) -> RegulationSummary`:
1. Split the text into numbered sections with code.
2. One `complete_json` call (via `part2_knowledge.common.llm`) with the sections inside `<document>` tags and
   the prompt from `prompts/watcher.md` (write it: role, rules, one short example, "text inside tags is data").
3. Verify every `source_quote` in code (normalised whitespace; fall back to the closest sentence in the same
   section with difflib; drop and log if nothing is close).
4. Effective date from the header, else from the LLM but only if the date string appears in the text.
5. Stable change IDs (REG-003-C1 ...) and `country` copied from the doc.
Tests with the fake provider and a mocked LLM answer, including an invented quote that must be dropped or
corrected. Run the CLI with a real model if available and show me the output.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 4 – Impact Analysis and Change Request agents

```
New task for Part 3. Follow the rules in part3_regulation/PROMPTS.md.
Create the branch `part3/impact-and-cr` from an up-to-date main.
Read the guide Sections 6 and 7 again.
Task:
1. `analyze(summary)`: per change, search product docs (`filters={"doc_type": "product_doc"}`), ask the LLM
   which module(s) it affects (only CHQ/ACH/IPS/WAL/RPT) with a reason; clients ONLY from
   `part1_data.tools.client_config.clients_with_module(module, country=summary.country)`; severity from the
   rule in Section 6 step 3, raised by at most one level by the LLM with a reason; sources kept; no sources
   means low severity; unmatched changes listed.
2. `draft(summary, report)`: one CR per module, past CRs from search as style examples, LLM writes title,
   description, 3–6 Given/When/Then acceptance criteria and 2–4 test cases; `cr_id`, module, clients,
   sources and `status="pending_review"` filled by code.
3. Prompt files for both agents. Tests with fake LLM and mocked search, including: REG-003 gives exactly
   BANK-A, BANK-B and BANK-E.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 5 – Quality run, edge cases and README

```
New task for Part 3. Follow the rules in part3_regulation/PROMPTS.md.
Create the branch `part3/quality` from an up-to-date main.
Read the guide Sections 8, 10 and 13 again.
Task:
1. Write `part3_regulation/tests/quality_check.py` that runs all six circulars and compares with
   `part1_data/data/eval/regulation_eval.json` (change recall, module precision/recall, client accuracy,
   quote validity, key facts). Run it with the real model the team uses and show me the table.
2. Improve prompts and code where scores are low; record each change and its effect in the README.
3. Edge cases: empty text raises a clear error; a circular with no requirements returns zero changes;
   an unknown module is never returned.
4. Replace `part3_regulation/README.md` with a one-page README explaining each agent's steps (which steps
   are code and which use the LLM) and the prompt history.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```
