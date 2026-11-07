# Part 2: Knowledge Base and AI Foundation

**Owner:** (khadija hzayen . khadija hzayen)
**Guide:** [Part 2 guide](../docs/source/02-Part2-Knowledge-Base-and-AI-Foundation.md)
**Delivery:** SearchResult, shared AI foundation and per-template ingestion/search

Part 2 provides the shared AI foundation: settings, template-based prompts, one LLM
wrapper and document search with a separate Chroma collection for each organization.
Delivered so far: the **SearchResult contract, settings, fake LLM, prompt rendering
and real per-template ingestion/search**. Real LLM providers are still planned.

## Completed work

- Audited Part 1 and both fictional datasets. Its 100 tests continue to pass.
- Added [SearchResult](../contracts/schemas.py), with described fields, bounded
  scores, the actual AC04 excerpt and compatible metadata for historical citations.
- Added shared `.env` settings, validated fake LLM responses, template-label prompt
  rendering and UTF-8 prompt loading. See [team usage rules](common/README.md).
- Replaced the stubs in [search.py](knowledge_base/search.py) and
  [ingest.py](knowledge_base/ingest.py) with persistent cosine Chroma collections.
  The loader covers documents, reason codes, units, stakeholders, historical
  requests/actions and change documents. Records, open requests and eval stay out.
- Added heading/numbered-section chunking, 800-character bodies with 100-character
  overlap for long sections, context prefixes, stable `source#index` IDs and source
  metadata including `template_id`. Shared policy sections retain `doc_type=document`.
- Search uses the selected/active template, combines filters with `$and`, and
  returns cited `SearchResult` objects. Scores are `1 - cosine_distance`, clipped
  to 0–1 and rounded to three decimals; empty indexes name the rebuild command.
- Added tests and updated [PR text](PR_DESCRIPTION.md) and [AI_LOG.md](AI_LOG.md).

## Using the foundation

Use Part 1's `load_template()` for labels. Omitted search template IDs use
`settings.active_template`; `ingest_all(None)` rebuilds all templates.

Use `LLM_PROVIDER=fake` in the project `.env`. External environment values win;
changes to `.env` require a process restart. Other provider names are recognized by
settings but raise `LLMError` until implemented.

## Rebuild and search

Run from the project folder with the existing environment. Each selected collection
is deleted and recreated in `settings.chroma_dir` (default `runtime/chroma`). Chroma's
local MiniLM embedding model downloads about 80 MB into its standard cache on first
use; subsequent ingestion/search uses that cached model. No LLM API key is needed.

```powershell
.\.venv\Scripts\python.exe -m part2_knowledge.knowledge_base.ingest
.\.venv\Scripts\python.exe -m part2_knowledge.knowledge_base.ingest --template university
```

The CLI and `ingest_all()` report files, chunks by type and elapsed seconds. Sources
and embeddings are prepared before the previous collection is removed.

```python
from part2_knowledge.knowledge_base.search import search
results = search("PREREQ_MISSING", template_id="university",
                 filters={"doc_type": "reason_codes", "reason_code": "PREREQ_MISSING"})
```

Verified real indexes: **payments: 15 files / 89 chunks; university: 15 files / 63
chunks**. AC04 and PREREQ_MISSING retrieval was verified in a fresh process.
Add a valid folder under `settings.templates_dir` and run ingestion to create
`kb_<template_id>` without code changes. Follow Part 1's format: bare code headings
and unit IDs in unit-specific filenames. A third-template test verifies discovery.

## Verification

Run from `projects/Regulatory-Support-Copilot/` with the existing environment:

```powershell
.\.venv\Scripts\python.exe -m pytest part2_knowledge/tests -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Last full validation (2026-11-07): **80 Part 2 tests passed; 180 tests passed overall**.
Tests use temporary collections and tiny local embeddings without downloads.
Real MiniLM ingestion/search was checked separately on Chroma 1.5.9. Full hit@5
evaluation and tuning remain a later task.

## Team review and remaining work

This delivery combines the Part 2 contract, foundation and ingestion/search work.
Integration into `main` was explicitly requested by the owner. Team-review approval
is not inferred from that request; see [review notes](CONTRACT_REVIEW.md).
The current identity masking fallback does not protect personal data.

Next: Ollama, Anthropic and OpenAI with JSON retries and real masking; then hit@5
evaluation (target ≥80% for each template) and tuning.
