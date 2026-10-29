# Part 2: Knowledge Base and AI Foundation

**Owner:** (write your name and GitHub username)
**Guide:** `docs/02-Part2-Knowledge-Base-and-AI-Foundation.pdf`
**AI tool prompts:** `PROMPTS.md` in this folder

Document search (RAG with one Chroma collection per template), the only LLM wrapper, settings, and prompt rendering with template labels.

```
part2_knowledge/
knowledge_base/ – ingest.py, search.py
common/         – config.py, llm.py, prompting.py
tests/
```

Only the owner edits this folder. Other parts use it only through the public functions listed in
`docs/00-Project-Guide.pdf`, Section 8.2. Replace this file with your own one-page README
(what the part does, inputs and outputs, how to run and test it).
