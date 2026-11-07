# Part 2: Knowledge Base and AI Foundation

**Owner:** (khadija hzayen . khadija hzayen)
**Guide:** [Part 2 guide](../docs/source/02-Part2-Knowledge-Base-and-AI-Foundation.md)
**Branch:** `part2/contract-searchresult`

Part 2 provides the shared AI foundation: settings, template-based prompts, one LLM
wrapper and document search with a separate Chroma collection for each organization.
The current delivery is the **SearchResult contract and its tests**; the remaining
services are still planned.

## Completed work

- Reviewed the project guides, all part READMEs, shared contracts, and Part 1's
  tools, connectors and both template datasets. Part 1's 100 tests passed, including
  deterministic record generation and data consistency checks.
- Added [SearchResult](../contracts/schemas.py) only in Part 2's contract section:
  `text`, `source`, `doc_type`, `location`, `score` and `metadata`, each described.
  Its realistic AC04 example quotes the payments source and includes `template_id`.
- Enforced scores from 0 to 1, rejecting invalid and non-finite values. Kept source
  categories and metadata extensible and compatible with existing history citations.
- Added [13 contract tests](tests/test_contracts.py) covering the source excerpt,
  JSON round-trip, field descriptions, score validation and both templates.
- Recorded contract decisions, description recommendations and draft teammate issues
  in [CONTRACT_REVIEW.md](CONTRACT_REVIEW.md); prepared [PR text](PR_DESCRIPTION.md)
  and updated [AI_LOG.md](AI_LOG.md). The initial implementation was committed as
  `14d115e` and pushed to the branch above.

## Verification

Run from `projects/Regulatory-Support-Copilot/` with the existing environment:

```powershell
.\.venv\Scripts\python.exe -m pytest part2_knowledge/tests -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Last full validation (2026-11-07): **13 Part 2 tests passed; 113 tests passed overall**.
These checks use no LLM or embedding model; search quality has not been measured yet.

## Team review and remaining work

All five members must review the shared contract. Review notes flag missing Parts
3–5 models, Part 5's masking function, evaluation-format agreement, action-storage
scope validation and remaining CODEOWNERS placeholders. They also propose clipping
negative cosine similarities to zero to respect the agreed score range.

Next: settings and fake LLM/prompting interfaces; per-template ingestion and search;
real LLM providers with retries and masking; then hit@5 evaluation (target ≥80% for
each template), tuning and team usage documentation. Records and open requests stay
outside the vector index. Other owners' code and contract sections were left unchanged.
