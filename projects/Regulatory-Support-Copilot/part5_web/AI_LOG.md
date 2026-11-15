# AI tool log – Part 5

Main prompts used with your AI coding tool, and what you changed by hand (Project Guide, Section 12).

| Date | Tool | Prompt (short) | What I kept / changed |
| --- | --- | --- | --- |
| 2026-11-15 | Claude Code | Build Part 5 from the part guide: contracts, masking, audit, review rules, website, JSON API, evaluation, tests, docs. | Kept FastAPI + Jinja2 + one CSS + plain JS; reused Part 4's SQLite file and public functions only. Fixed by testing: IBAN rule no longer masks reason-code sequences such as "BE04 RJCT AC04". |
