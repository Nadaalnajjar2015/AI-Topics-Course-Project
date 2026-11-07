## What this PR does

Adds the missing `SearchResult` contract so Parts 3–5 can use one shared shape for
retrieved evidence. Its six required fields have descriptions, and its payments
example quotes the actual AC04 passage with `template_id` in metadata.

Scores are bounded to 0–1 and invalid/non-finite values are rejected. Source types
and metadata remain extensible; existing historical citations from both templates
still validate. `CONTRACT_REVIEW.md` records the proposed handling of negative
cosine similarity, description recommendations and draft teammate issues.

Changes to shared schemas are limited to Part 2's section, under the authorized
Contract Day exception. The pre-existing README owner-name edit stays uncommitted.
Settings, LLM access, prompt rendering and ingestion/search follow in later PRs.

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

**13 Part 2 tests passed; 113 tests passed in the full suite.** Tests cover the
AC04 excerpt against its actual source, JSON round-trip, every field description,
score limits and invalid values, university evidence, and compatibility with all
six historical source citations. Part 1's original 100 tests continue to pass.
No new dependency, model download or external LLM call is needed.

## Screenshots (for website changes)

Not applicable; this is a shared Python contract change.

## Contract changes?

- [ ] No
- [x] Yes – all five members must approve

Please review the six fields and the proposed cosine-score interpretation in
`CONTRACT_REVIEW.md`. No issue is linked; teammate issue texts are drafts only.
