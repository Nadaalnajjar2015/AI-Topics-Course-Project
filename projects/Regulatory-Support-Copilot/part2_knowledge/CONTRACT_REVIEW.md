# Part 2 Contract Day review

Prepared on 2026-11-07. This change adds only `SearchResult` in Part 2's section of
`contracts/schemas.py`; every other owner's contract section stays unchanged.

## SearchResult decisions

- Keep the six agreed fields: `text`, `source`, `doc_type`, `location`, `score`, and
  `metadata`. Every field is required and described for structured LLM output.
- The payments example quotes the real AC04 section in `reason_codes.md`, with
  `template_id: payments` and `reason_code: AC04` in metadata.
- Keep `doc_type` as a string and metadata as a dictionary so another organization
  can add source categories without editing the shared model.
- New search results must carry `template_id`. Existing historical citations lack
  it, so the model accepts them; ingestion will add ownership to new chunks.
- Enforce the Project Guide's score range of 0–1, including rejection of non-finite
  values. Scores measure retrieval similarity, not confidence in an answer.
  Section 8.5 also requests `1 - cosine_distance`, which can be negative. Proposed
  resolution for the later search implementation: calculate that value, clip to
  0–1, and round to three decimals. Preserve distance order when ranking results.
  All five members should review this interpretation before search is implemented.

## Suggested description improvements for other owners

These are recommendations only; their contract sections were not edited.

| Owner / fields | Suggested clarification |
| --- | --- |
| Part 1: `TemplateConfig.labels` | List the required general label keys and how they map to prompt placeholders. |
| Part 1: `TemplateConfig.action_item_fields` | State that entries are shared ActionItem field names, and whether values must be nonempty. |
| Part 1: `Stakeholder.attributes`, `ChangeDocument.scope` | Describe scalar/list attribute types and all/type/boolean/key=value matching with examples. |
| Part 1: timestamps and dates | Specify ISO 8601 formats and the timezone convention; distinguish scenario time from today's date. |
| Part 1: `Record.status`, `Request.priority` | Explain template-defined vocabulary and how successful status relates to a null reason code. |
| Part 3: requirements, impacts, action items (not implemented yet) | Describe exact source quotes, valid template IDs for units/stakeholders, severity values, and human-review status. |
| Part 4: investigation and task models (not implemented yet) | Describe evidence provenance, null-item/code cases, escalation for unspecified causes, confidence rules, and task output keys. |
| Part 5: review/audit models (not implemented yet) | Describe decision values, edited content, actor/template ownership and timestamp formats. |

## Draft teammate issues

No issues or messages have been posted.

**Part 1 — apply change scope at the action-storage boundary**

`create_action_item()` checks unit membership without passing the change's scope
to `stakeholders_for_unit()`. BANK-C belongs to ACH but is outside CHG-P-002's
Country X scope. Apply the loaded change's scope when validating stakeholders.
Acceptance: reject an approved item containing an out-of-scope stakeholder, while
preserving valid items for both templates. Part 2 has not edited Part 1.

**Part 5 — supply masking and confirm evaluation envelopes**

Provide `part5_web.safety.masking.mask(text)` and confirm that evaluation consumers
iterate the `cases` array inside the documented JSON envelope. A mocked masking
hook can verify Part 5 wiring, but cannot prove the missing Part 5 implementation.
Part 2 now applies strict local redaction even without this module. Acceptance: real
masking tests cover both templates, and evaluation reads all current cases.

**Team — complete contracts, ownership and guide corrections**

Parts 3–5 must supply their own described models and validating examples. Replace
the remaining CODEOWNERS placeholders. CHG-U-001 includes STU-INTL under the scope
rules; P-REQ-016 escalates despite having a documented MS03 record. Align the guide
examples with those fixtures. Review the score interpretation above on Contract Day.

## Remaining Part 2 work

Settings, fake LLM and prompting were delivered on `part2/config-llm-prompting`.
`part2/ingestion-and-search` replaces its stubs with real per-template retrieval
(80 Part 2 / 180 total tests pass). The owner explicitly requested integrating this
combined delivery into main; this does not assert that team-review approvals were
recorded. Search clips negative cosine similarity to zero as proposed above.
The `part2/privacy-search-quality` review branch adds strict Part 2 privacy and a
real-model Hit@5 gate: 12/12 per template, with 144 Part 2 / 244 total tests passing.
The owner has confirmed committing, publishing a PR and integrating that work into main.
Real LLM providers and integration with the actual Part 5 module remain pending.
Records and open requests are not vector-index sources; scenario dates remain evidence.

## Validation

Run from `projects/Regulatory-Support-Copilot/` using the existing project environment:

```powershell
.\.venv\Scripts\python.exe -m pytest part2_knowledge/tests -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Initial contract PR results on 2026-11-07: **13 Part 2 tests passed; 113 tests passed in the full suite**.
The contract tests check the real AC04 excerpt, JSON round-trip, schema descriptions,
score boundaries and invalid/non-finite scores, university evidence, and all six
existing historical action citations. No LLM or embedding model is called.
