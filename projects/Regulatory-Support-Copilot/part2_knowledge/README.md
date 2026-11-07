# Part 2: Knowledge Base and AI Foundation

**Owner:** (khadija hzayen . khadija hzayen)
**Guide:** [Part 2 guide](../docs/source/02-Part2-Knowledge-Base-and-AI-Foundation.md)
**Branch:** `part2/config-llm-prompting`

Part 2 provides the shared AI foundation: settings, template-based prompts, one LLM
wrapper and document search with a separate Chroma collection for each organization.
Delivered so far: the **SearchResult contract, settings, fake LLM, prompt rendering
and integration stubs**. Real retrieval and real model providers are still planned.

## Completed work

- Audited Part 1 and both fictional datasets. Its 100 tests continue to pass.
- Added [SearchResult](../contracts/schemas.py), with described fields, bounded
  scores, the actual AC04 excerpt and compatible metadata for historical citations.
- Added [config.py](common/config.py): typed shared settings, project-local `.env`
  loading, absolute paths resolved from the project folder, and runtime creation.
- Added [llm.py](common/llm.py): `complete_text()` returns fixed offline text;
  `complete_json()` validates a fresh copy of the requested contract's example.
  Both use Part 5's masking hook when available, otherwise an identity fallback.
- Added [prompting.py](common/prompting.py): `render()` fills both templates' labels
  and extra values, naming unknown placeholders; `load_prompt()` reads UTF-8 files.
- Added [search.py](knowledge_base/search.py) and [ingest.py](knowledge_base/ingest.py)
  stubs. Search returns the payments contract example only for its owning template
  and matching filters; other templates return no hits. Ingestion reports `stub`
  summaries for one/all templates and builds no index.
- Added settings, LLM, prompting and stub tests; updated [team usage rules](common/README.md),
  [PR text](PR_DESCRIPTION.md) and [AI_LOG.md](AI_LOG.md).

## Using the foundation

Parts 3–5 can import `settings` from `part2_knowledge.common.config`,
`complete_json`/`complete_text` from `common.llm`, and `render`/`load_prompt` from
`common.prompting` under the same package. Use Part 1's `load_template()` to obtain
labels. Omitted template IDs use `settings.active_template`; `ingest_all(None)`
instead describes all templates. See [common/README.md](common/README.md) for examples.

Use `LLM_PROVIDER=fake` in the project `.env`. External environment values win;
changes to `.env` require a process restart. Other provider names are recognized by
settings but raise `LLMError` until implemented. The ingestion command currently
prints an explicit stub message:

```powershell
python -m part2_knowledge.knowledge_base.ingest --template university
```

## Verification

Run from `projects/Regulatory-Support-Copilot/` with the existing environment:

```powershell
.\.venv\Scripts\python.exe -m pytest part2_knowledge/tests -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Last full validation (2026-11-07): **52 Part 2 tests passed; 152 tests passed overall**.
These checks use no LLM or embedding model; search quality has not been measured yet.

## Team review and remaining work

The contract branch is not merged into `main` yet; this branch carries its existing
commits as a dependency. All five members must review that contract. Foundation
changes edit only Part 2. [CONTRACT_REVIEW.md](CONTRACT_REVIEW.md) retains teammate
issues and the proposed cosine-score interpretation. The identity masking fallback
is an offline integration aid, not working personal-data protection.

Next: real per-template ingestion/search; Ollama, Anthropic and OpenAI with JSON
retries and real masking; then hit@5 evaluation (target ≥80% for each template) and
tuning. New template folders will get collections through the future ingestion
implementation. Records and open requests stay outside the vector index.
