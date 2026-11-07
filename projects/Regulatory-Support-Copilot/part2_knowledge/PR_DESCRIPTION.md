## What this PR does

Delivers Part 2's shared AI foundation and real per-template Chroma retrieval.
Adds typed `.env` settings, validated offline `complete_text()`/`complete_json()`,
template-label prompt rendering and UTF-8 prompt loading. The fake LLM uses fresh
copies of contract examples; actual model providers remain a later task.

Adds the six-field `SearchResult` contract in Part 2's shared-schema section, with
field descriptions, score bounds and the real AC04 example including template
metadata. No other owner's model section or part folder is changed.

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
test and documentation changes are inside `part2_knowledge/`, with the earlier
authorized SearchResult Contract Day exception in `contracts/schemas.py`. No new
library is added. Both prompt strings use Part 5's masking hook when available;
the current identity fallback is an offline integration aid, not real masking.

This integration PR includes the existing `part2/contract-searchresult`,
`part2/config-llm-prompting` and `part2/ingestion-and-search` work together. The owner
explicitly requested creating the PR and merging this delivery into main. That
authorization is not a claim that all five members' review approvals were recorded.

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
- [x] Yes – Part 2's SearchResult model; shared contract review applies

The shared-schema change is limited to Part 2's SearchResult section. Integration
documentation edits are confined to `part2_knowledge/`.
No issue is linked; teammate issue texts remain drafts in `CONTRACT_REVIEW.md`.
