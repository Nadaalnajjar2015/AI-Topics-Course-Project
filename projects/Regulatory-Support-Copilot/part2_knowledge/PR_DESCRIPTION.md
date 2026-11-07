## What this PR does

Unblocks Parts 3–5 with shared typed settings, offline `complete_text()` and
`complete_json()`, template-based `render()` and UTF-8 `load_prompt()`, plus the
documented search and ingestion interfaces. Settings load the project `.env`,
respect environment precedence, resolve paths from the project folder and create
`runtime/`. Fake JSON results validate the schema example without mutating it.

Both prompts use Part 5's masking hook when available; until then an identity
fallback supports offline integration. Other providers fail clearly. Search only
returns the payments contract example for its owning template and matching filters;
university returns no hits until real retrieval exists. Ingestion summaries and CLI
output explicitly say that no index was built. README and team usage rules describe
these limits. No new dependencies or new shared-schema edits were made.

Dependency: `part2/contract-searchresult` has not been merged into `main`. This
branch was created from updated main and fast-forwarded through its existing
contract commits. Review foundation changes against that branch, or merge the
contract PR first and bring updated main into this branch before merging. This
does not constitute approval of the contract.

## Which part

- [ ] Part 1
- [x] Part 2
- [ ] Part 3
- [ ] Part 4
- [ ] Part 5

## How I tested it

From `projects/Regulatory-Support-Copilot/`, using the existing `.venv`:

```powershell
.\.venv\Scripts\python.exe -m pytest part2_knowledge/tests -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

**52 Part 2 tests passed; 152 tests passed in the full suite.** New tests cover
settings defaults, `.env` precedence, path resolution, runtime creation, active
template integration with Part 1, all seven current contract examples, fresh fake
responses, missing/invalid examples, masking hook/fallback and dependency errors,
unavailable providers, all template labels, unknown placeholders, UTF-8 prompts,
stub filters/template isolation and ingestion CLI output. Part 1's original 100
tests and the 13 contract tests continue to pass. No model download or LLM call is
needed; real search quality and real masking are not claimed.

## Screenshots (for website changes)

Not applicable; this is shared Python infrastructure.

## Contract changes?

- [ ] No
- [x] Yes – inherited contract dependency; all five members must approve it

No schema changes beyond the existing contract branch. The foundation commit edits
only `part2_knowledge/`; the contract dependency still requires its own team review.
No issue is linked; teammate issue texts remain drafts in `CONTRACT_REVIEW.md`.
