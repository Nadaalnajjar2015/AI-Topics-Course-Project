# Part 2: AI tool prompts

Five prompts for the owner of `part2_knowledge/` to give, one at a time, to their own AI coding tool (Claude Code, Cursor, Copilot, ChatGPT, …). Open the tool **inside the repository folder** `AI-Topics-Course-Project` so it can read every file.

**How to use them**

- Give Prompt 1 first, in a new chat. It makes the tool study the whole project before it touches anything.
- Give the next prompt only after the previous pull request is merged (or at least pushed and reviewed).
- For every later prompt, start a fresh chat and paste the short **Start of every session** text first, then the prompt.
- Read and understand every line the tool writes. You present and defend this code.

## Start of every session (paste before Prompts 2–5)

```
You are my coding assistant for Part 2 (Knowledge Base and AI Foundation) of a 5-person student project.
Before doing anything: go to projects/ProgressSoft-Regulatory-Copilot/, run `git checkout main` and
`git pull`, list the folder tree, then read README.md, docs/source/00-Project-Guide.md, docs/source/02-Part2-Knowledge-Base-and-AI-Foundation.md,
contracts/schemas.py and part2_knowledge/PROMPTS.md. Follow the "Rules for the AI tool" in that file.
Then check what already exists in my folder and in the other part folders that I depend on,
summarise it in 5 lines, and wait for the task.
```

## Rules for the AI tool (it reads these every time)

1. **Where to work.** The Git repository is `AI-Topics-Course-Project`. The project lives in
   `projects/ProgressSoft-Regulatory-Copilot/`. Run every command from that folder.
2. **Your folder.** Edit only `part2_knowledge/`. Never edit another part's folder, `docs/`, or
   `contracts/schemas.py` (except the Contract Day prompt, and then only this part's own section).
   If something outside this folder needs to change, stop and write me a short GitHub Issue text instead.
3. **Other parts.** Use other parts only through their public functions in the Project Guide,
   Section 8.2. If a function does not exist yet, use its stub, or a small fake inside this part's tests.
4. **Read before writing.** The guides are Markdown files you can read:
   `docs/source/00-Project-Guide.md` and `docs/source/02-Part2-Knowledge-Base-and-AI-Foundation.md`. Follow them exactly.
5. **Stack.** Python 3.11+, Pydantic v2, pytest. Follow the contracts in `contracts/schemas.py`.
   No new library without asking me; if I agree, add it to `requirements.txt`.
6. **Plan first.** Before writing code, show me a short plan (files, functions, tests) and wait for my "go".
7. **Small and tested.** Small functions with short comments. Every public function gets pytest tests in
   `part2_knowledge/tests/`. Run `pytest part2_knowledge/tests` and show me the result before committing.
8. **Git.** Never commit to `main` and never force-push. Start each task from an up-to-date `main`:
   `git checkout main`, `git pull`, then `git checkout -b <branch name from the prompt>`.
   Commit messages look like `feat(part2): ...`, `test(part2): ...` or `fix(part2): ...`.
   When done, `git push -u origin <branch>` and give me a pull request title and description that
   fills `.github/pull_request_template.md` (or open it with `gh pr create` if `gh` is installed).
9. **Safety.** Never put API keys or secrets in code or commits. `.env` is never committed.
   All data is fictional (Project Guide, Section 9).
10. **Log.** Add one line to `part2_knowledge/AI_LOG.md` for this task (date, tool, short prompt, what we kept or changed).
11. **Finish with a report:** files changed, how to test, what is left, and any questions or Issues for teammates.

## Prompt 1 – Study the whole project, then the Contract Day work

```
You are my coding assistant for Part 2 (Knowledge Base and AI Foundation) of a 5-person student project, the
"Regulatory & Support Copilot". All five students work in the same GitHub repository, each in their
own part folder, each with their own AI tool.

Step 1 – Understand the whole project before doing anything:
- Make sure you are in `projects/ProgressSoft-Regulatory-Copilot/` and run `git checkout main` and `git pull`.
- List the whole folder tree (all folders and files, except .git and .venv) and tell me what each
  top-level folder is for and who owns it.
- Read `README.md`, `docs/source/00-Project-Guide.md` (all of it), `docs/source/02-Part2-Knowledge-Base-and-AI-Foundation.md` (all of it),
  `contracts/schemas.py`, `contracts/CONTRACTS.md`, the repository's `../../.github/CODEOWNERS`,
  and the README of every part folder.
- Skim the other four part guides in `docs/source/` so you know what my teammates build and what they
  expect from me.
- Read `part2_knowledge/PROMPTS.md` and follow its "Rules for the AI tool" in everything you do.

Step 2 – Report back to me (no code yet):
- A 10-line summary of the project and of my part.
- What my part must deliver, who depends on it, and what it depends on (with function names).
- The files you plan to create in `part2_knowledge/`, in the order the guide's week plan suggests.
- Anything unclear or contradictory in the guides.

Step 3 – Then do this first task on branch `part2/contract-searchresult`:
- Write my contract model `SearchResult` in the Part 2 section of `contracts/schemas.py`, every field with
  `Field(description=...)` and a realistic example (a chunk from `reason_codes.md`). Add a test that the
  example validates.
- Suggest in your report which contract fields of other parts need better descriptions for LLM JSON output
  (I will raise them on Contract Day; do not edit their sections).
```

## Prompt 2 – Config and the LLM wrapper with the fake provider (urgent)

```
New task for Part 2. Follow the rules in part2_knowledge/PROMPTS.md.
Create the branch `part2/config-and-llm-fake` from an up-to-date main.
Read the guide Sections 5 and 6 again. Teammates are blocked until this exists.
Task:
1. `part2_knowledge/common/config.py`: load `.env` with python-dotenv and expose one `settings` object with
   the fields and defaults in Section 5; create `runtime/` if missing.
2. `part2_knowledge/common/llm.py` with `complete_text(system, user)` and `complete_json(system, user, schema)`,
   only the `fake` provider for now: it returns the schema's `json_schema_extra` example (or a fixed string).
   Call `mask()` from `part5_web.safety.masking` if it exists; otherwise use a local identity fallback.
3. `part2_knowledge/knowledge_base/search.py` with a `search(query, k=5, filters=None)` stub returning the
   SearchResult example, and an `ingest.py` stub with `ingest_all()`.
4. Tests: `complete_json` returns a valid instance for every model currently in `contracts/schemas.py`.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 3 – Ingestion and real search

```
New task for Part 2. Follow the rules in part2_knowledge/PROMPTS.md.
Create the branch `part2/ingestion-and-search` from an up-to-date main.
Read the guide Section 7 again and look at the real files in `part1_data/data/`.
Task:
1. `ingest.py`: load every source in the table of Section 7.1, chunk by headings (800 chars, 100 overlap for
   long sections, context prefix), add the metadata keys, use stable chunk IDs, and rebuild the Chroma
   collection `copilot_kb` (cosine) in `settings.chroma_dir`. `python -m part2_knowledge.knowledge_base.ingest`
   prints a summary; `ingest_all()` returns it as a dict.
2. `search.py`: real search with metadata filters (use `$and` for several keys), score = 1 - distance,
   clear error when the collection is empty.
3. Unit tests for chunking (heading split, long-section split, stable IDs) and search on a tiny temporary
   collection (filters, empty collection).
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 4 – Real providers, retries and masking

```
New task for Part 2. Follow the rules in part2_knowledge/PROMPTS.md.
Create the branch `part2/llm-providers` from an up-to-date main.
Read the guide Sections 6.2–6.4 again and the current `llm.py`.
Task:
1. Add the `ollama` provider (HTTP to `/api/chat`, JSON format), then `anthropic` and `openai` using their
   official packages; each as a small private function; temperature 0; timeout from settings.
2. JSON handling: strip code fences, validate with the schema, retry once with the validation error,
   then raise `LLMError` with a clear message.
3. Masking: both system and user text go through `mask()` before any provider is called.
4. Logging of provider, model, duration and success (no full prompts).
5. Tests with a mocked provider: bad-then-good JSON succeeds, bad twice raises LLMError, the provider receives
   masked text. Show me one real call with Ollama if it is installed.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```

## Prompt 5 – Search quality, tuning and team rules

```
New task for Part 2. Follow the rules in part2_knowledge/PROMPTS.md.
Create the branch `part2/search-quality` from an up-to-date main.
Read the guide Sections 6.4, 8 and 10 again.
Task:
1. `part2_knowledge/tests/test_search_quality.py`: run every query in `part1_data/data/eval/search_eval.json`,
   compute hit@5, print a table of failures, and fail below 0.8.
2. If below target, try the ideas in Section 8 one at a time (smaller chunks, prefix, filters, hybrid search
   for exact codes such as AC04). Record every try and its score in `part2_knowledge/README.md`.
3. Replace `part2_knowledge/README.md` with a one-page README (what the part does, how to rebuild the index,
   how to switch LLM provider) and write `part2_knowledge/common/README.md` with the LLM rules for the team
   from Section 6.4.
Plan first and wait for my go. When done: run the tests, commit, push the branch,
give me the pull request text, update AI_LOG.md, and report what is left.
```
