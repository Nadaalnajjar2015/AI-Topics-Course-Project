## What this PR does

Replaces the Part 2 ingestion/search stubs with real per-template Chroma retrieval.
Both templates now load documents, code sections, units, stakeholders, historical
requests/actions and numbered change sections into isolated `kb_<template_id>`
collections. Records, open requests and evaluation cases stay outside the index;
unnumbered change background is excluded from change-clause chunks.

Chunks have heading context, 800-character bodies, 100-character overlap for long
sections, stable source/index IDs and scalar metadata including template ownership.
University general-policy sections remain searchable as documents while bare code
headings receive reason-code metadata. Unit metadata comes from configured unit IDs
in filenames. Sources and embeddings are prepared before replacing an old collection.

Search uses cosine distance, `$and` equality filters, explicit/active template
selection, clipped/rounded 0–1 scores and actionable empty-index errors. CLI and
`ingest_all()` return file counts, chunks per type and timings. All new source,
test and documentation changes are inside `part2_knowledge/`; no new library or
new shared-schema edit is included.

Dependency: this branch starts from updated main and carries the existing
`part2/config-llm-prompting` and contract commits, which remain unmerged. Review the
new changes against `part2/config-llm-prompting`, or merge prerequisites and bring
updated main into this branch before merging. The inherited contract still needs
all five members' review; these changes do not constitute that approval.

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
.\.venv\Scripts\python.exe -m part2_knowledge.knowledge_base.ingest
```

**80 Part 2 tests passed; 180 tests passed overall, without warnings.** Coverage
includes heading/long-section splits, overlap, stable IDs, all seven source types,
mixed policy/code documents, source exclusions, metadata filters, cosine scores,
template isolation, missing/empty collections, stale-chunk removal, preservation of
the old index on source/embedding failures, CLI summaries and third-template
ingestion/search. Tests use temporary collections and tiny local embeddings.

Separately ran real MiniLM ingestion on Chroma 1.5.9: payments **15 files / 89
chunks**, university **15 files / 63 chunks**. A fresh process retrieved the actual
AC04 and PREREQ_MISSING sections with the correct template metadata; the SE301
search also returned its study-plan source. The first run downloaded Chroma's
standard local embedding model. Runtime/model files are not committed. Full hit@5
evaluation and tuning remain a later task; no LLM-provider call was made.

## Screenshots (for website changes)

Not applicable; this is Part 2 Python infrastructure.

## Contract changes?

- [ ] No
- [x] Yes – inherited contract dependency; all five members must approve it

No new schema changes beyond the existing contract branch. This task edits only
`part2_knowledge/`; the contract dependency still requires its own team review.
No issue is linked; teammate issue texts remain drafts in `CONTRACT_REVIEW.md`.
