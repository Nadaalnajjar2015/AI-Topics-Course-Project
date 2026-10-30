# Draft teammate issues

These are issue texts for review; no GitHub issues or messages have been posted.

## Part 2: supply settings and SearchResult contracts

Labels: `part-2`, `contract`, `integration`

Please implement the documented `part2_knowledge.common.config.settings` object with `active_template` and `templates_dir`, and the `SearchResult` model in Part 2's section of `contracts/schemas.py`. Part 1's tools are ready and use explicit template IDs today. When the settings module is absent, only the documented defaults (`payments`, `part1_templates/templates`) are used; Part 1 does not independently read `.env` or environment variables. Once your module exists, the tools use its settings automatically. SearchResult is also a dependency of Part 3's action sources.

Acceptance: changing `settings.active_template` changes Part 1's calls with `template_id=None`; explicit IDs remain isolated. Unit, stakeholder and history ingestion should read the JSON envelopes documented in `part1_templates/templates/README.md`.

## Part 3: supply Check and ActionItem contracts

Labels: `part-3`, `contract`, `integration`

Please implement `Check` and `ActionItem` in your own section of `contracts/schemas.py`, with field descriptions and a realistic example, according to Project Guide 8.1. Part 1's action storage validates against this shared model at call time and refuses unapproved items. Until the model exists, creating actions raises an explicit dependency error; empty action lists still work. Part 1 uses a test-only fake for isolated storage tests and has not modified your contract section.

Acceptance: an approved ActionItem round-trips through `create_action_item()` and `list_action_items()` in its template; pending/rejected items are refused. Review the historical examples under both templates. For CHG-U-001, use STU-CS-2026, STU-SE-2026 and STU-INTL: Guide 1's table and scope rule include international students; one example in Guide 3 omits them.

## Part 5: agree evaluation collection envelopes

Labels: `part-5`, `question`, `integration`

Please confirm the Section 10 evaluation case format with a JSON collection envelope `{"_note": "MOCK DATA – fictional, for a student prototype", "cases": [...]}`. Each case retains the exact documented keys. Payments has 5 change / 15 request / 12 search cases; university has 3 / 10 / 8. The envelope satisfies the mandatory mock marker without inserting a non-case row into a case list. Your runner should iterate `json.load(stream)["cases"]`.

Acceptance: the evaluation runner consumes both sets; no-record cases escalate, general questions use documents, and the prompt-injection requests retain their planted failure reasons. Real agent accuracy and safety outcomes remain Parts 3–5 integration work; Part 1 tests only establish consistent evidence and expected answers.
