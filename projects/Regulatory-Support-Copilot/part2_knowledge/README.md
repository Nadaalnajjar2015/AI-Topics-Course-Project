# Part 2: Knowledge Base and AI Foundation

**Owner:** (khadija hzayen . khadija hzayen)
**Guide:** [Part 2 guide](../docs/source/02-Part2-Knowledge-Base-and-AI-Foundation.md)
**Delivery:** Strict Part 2 privacy and per-template Hit@5 quality gate

Part 2 supplies the SearchResult contract, shared settings, fake LLM wrapper,
template prompts and isolated Chroma search. It indexes documents, reason codes,
units, stakeholders, history and numbered changes. Records, open requests and
evaluation answers stay outside the index. See [team interfaces](common/README.md).

## Privacy boundary

[privacy.py](common/privacy.py) fully replaces detected financial/contact/ID values
with `[REDACTED]`, including partial masks that retain digits. It uses strict local
redaction before/after Part 5's hook, with no identity fallback. A broken hook stops
processing with `PrivacyError`.

Protection covers prompts, schema examples/defaults, responses, full documents
before chunking, embedding input, stored IDs/metadata, queries and returned results.
Explicitly named private fields are hidden even when short. Short operational IDs
and validated ISO dates remain usable. Pattern rules are not a universal detector
of all personal information; Part 1 source fixtures remain unchanged.

## Rebuild and use

Run from `projects/Regulatory-Support-Copilot/`. Existing indexes without the current
privacy-policy marker are rejected until rebuilt. Rebuild replaces each selected
collection in ignored `settings.chroma_dir` (default `runtime/chroma`).

```powershell
.\.venv\Scripts\python.exe -m part2_knowledge.knowledge_base.ingest
.\.venv\Scripts\python.exe -m part2_knowledge.knowledge_base.ingest --template university
```

Local indexes were rebuilt on 2026-11-08: **payments 89 chunks; university 63**, from
15 source files each. The local MiniLM model needs an approximately 80 MB download
on first use; subsequent calls use its cache.

`search(query, k=5, filters=None, template_id=None)` returns cited results with cosine
scores clipped to 0–1. Omitted IDs use `settings.active_template`; `ingest_all(None)`
rebuilds all templates. Add a valid folder under `settings.templates_dir` and ingest
to create `kb_<template_id>` without code changes. Use Part 1's file conventions.

Use `LLM_PROVIDER=fake` in `.env`; restart after setting changes. Ollama, Anthropic
and OpenAI providers remain unimplemented and raise `LLMError`.

## Search quality and tests

[test_search_quality.py](tests/test_search_quality.py) builds fresh temporary indexes
with real MiniLM embeddings, runs every evaluation query unfiltered, and checks
exact expected source paths within the first five results. It prints each hit/miss
and fails independently below 80% for either template. Missing/empty eval data fails.

| Measured attempt (2026-11-08) | Payments Hit@5 | University Hit@5 |
| --- | --- | --- |
| Baseline: 800-char chunks, overlap 100, context prefix | 12/12 (100%) | 12/12 (100%) |
| Strict privacy at all Part 2 boundaries; same ranking | 12/12 (100%) | 12/12 (100%) |

No ranking/chunk tuning was needed. These are the supplied synthetic cases, not a
general accuracy guarantee. Quality tests require the cached/downloadable embedding
model; unit privacy/storage tests use local test embeddings.

```powershell
.\.venv\Scripts\python.exe -m pytest part2_knowledge/tests/test_search_quality.py -q
.\.venv\Scripts\python.exe -m pytest part2_knowledge/tests -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

**144 Part 2 tests / 244 total tests passed.** See [AI log](AI_LOG.md),
[PR draft](PR_DESCRIPTION.md) and [team follow-ups](CONTRACT_REVIEW.md).
The owner confirmed commit, PR publication and integration into main. Real providers
and whole-project integration with Part 5's actual masking module remain pending.
