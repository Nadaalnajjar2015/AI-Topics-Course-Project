# Part 1 review notes

The implementation was prepared on `zainbranch`. Shared-file changes are the six Part 1 models in `contracts/schemas.py`, authorized by the Contract Day prompt, and the user's later editor-warning annotation on the existing Pydantic import. No other part folder, guide, dependency list or contract section was edited. The user separately authorized committing the remaining change and merging into `main`.

## Delivered files

- Six models: TemplateConfig, Unit, Stakeholder, ChangeDocument, Record and Request, each with field descriptions and a validated payments example.
- Both complete template folders: YAML configuration, units, stakeholders, documents, changes, record generators and output, requests, history and three evaluation files.
- `tools/templates.py`, `changes.py`, `directory.py`, `requests.py`, `records.py`, `action_list.py` and private `_files.py`.
- Connector interface, shared JSONL mechanics, transaction/registration connectors and registry.
- Tests for both templates, including every public tool, error paths, all scope forms, connector filters, immutable fixtures, runtime isolation and seed reproducibility.
- Part 1 README, template-format README, AI log and draft teammate issues.

The final implementation includes real tools and full data rather than retaining the interim stubs and 80-record sample. All stages use `zainbranch` as requested.

## Guide Section 11 checklist

| Check | Payments | University | Evidence |
| --- | --- | --- | --- |
| Planted records match request person, item and reason | Pass | Pass | `test_planted_requests_match_records`; planned missing records remain absent |
| Every record reason has a `##` documentation section | Pass | Pass | `test_reason_codes_have_document_sections` |
| Unit IDs exist; bank records use enabled modules | Pass | Pass | `test_units_and_memberships_are_consistent` |
| Change stakeholders equal unit membership plus scope | Pass | Pass | `test_change_stakeholders_equal_scope_rule` |
| Requesters have records except planned escalations | Pass | Pass | `test_requesters_have_records_except_planned_escalations` |
| Dates are coherent | Pass | Pass | Publication/effective checks, planted records before requests, generator date windows |
| Configuration validates and regex extracts named items | Pass | Pass | Contract/config tests and `test_item_pattern_finds_every_named_item` |
| Names and personal-data fixtures are fictional | Reviewed | Reviewed | Guide's invented names; `.example` email, invalid `JO00 MOCK` IBAN, zero-prefixed mock ID and placeholder phone; no real data source used |
| Data files carry the mock marker | Pass | Pass | `test_markers_counts_history_and_sources`; JSON uses `_note`, circular marker follows front matter |

The scripts produce exactly 500 payment records (75 failures, 15%) and 250 registration records for 50 students. Reproducibility tests run each generator twice into temporary files and compare SHA-256 hashes with committed output. Historical action examples have known changes, correct scopes, concrete checks and document excerpts.

## Verify locally

Executed on 2026-10-30: **95 tests passed** in the Part 1 suite. The separate reproducibility run passed both template cases. Direct tool calls confirmed `T-100457 / AC04`, `R-48213 / PREREQ_MISSING`, and the CHG-P-002 stakeholder union BANK-A, BANK-B, BANK-E. Local documentation links resolve and `git diff --check` is clean.

| Generated file | SHA-256 of each of two runs and committed output |
| --- | --- |
| `payments/records/transactions.jsonl` | `879900e95a94227b57a6903df9fce2339bab9bbebb187ddde03f91ee4f59c831` |
| `university/records/registrations.jsonl` | `46c7774bfd78393b0985fec2bb03ec1b6bfd7672415c82b4d6fcbcf241a1464c` |

From `projects/Regulatory-Support-Copilot/`, with the existing project dependencies installed:

```powershell
.\part1_templates\.venv\Scripts\python.exe -m pytest part1_templates/tests
.\part1_templates\.venv\Scripts\python.exe -m pytest part1_templates/tests/test_template_consistency.py -k generators -s
```

Tests use temporary runtime directories. They do not update fixture files or populate the real runtime state. The environment used here is Python 3.15.1 with Pydantic 2.14.2, PyYAML 6.0.3 and pytest 9.2.0. On this interpreter, PyYAML was installed with its optional C extension disabled because the machine lacks C++ build tools; no dependency was added to requirements.txt. Other supported Python versions have not been tested here.

## Remaining integration and decisions

1. Part 2 must supply `config.settings` for `.env` loading and active-template switching. Explicit template IDs and default payments work now.
2. Part 3 must supply `ActionItem`/`Check`, with Part 2's `SearchResult` dependency. Action storage is implemented and tested with a test-only fake. Creating a real action remains unavailable until the shared model is supplied; the error names the missing dependency.
3. Part 5 must confirm the documented JSON `cases` envelope for evaluation. Case keys and counts follow the guide.
4. Contract changes require all five members' approval. Part 2 is the normal reviewer for Part 1. Agent, website, RAG, audit and LLM integration have not been tested because those implementations do not exist yet.

Draft copyable issue texts are in [TEAM_ISSUES.md](TEAM_ISSUES.md); they have not been posted. Pending/rejected actions cannot be stored, but approval of request status changes remains the caller's responsibility as defined by the guide.
