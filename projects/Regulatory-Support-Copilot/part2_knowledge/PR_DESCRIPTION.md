## What this PR does

Title: **fix(part2): protect private data and enforce per-template Hit@5**

Replaces the LLM identity fallback with strict full redaction at Part 2 boundaries.
Known IBAN, phone, account, card, national-ID and email formats become `[REDACTED]`,
including partial masks retaining digits. Explicitly named private fields are hidden.
Part 5's hook is used when present; failures stop processing instead of passing raw
data onward. The adapter remains effective while that module is absent.

Protects system/user prompts, schema examples/defaults, provider responses, complete
source text before chunking, embedding inputs, stored chunk IDs/metadata, search
queries/filters and returned evidence. Validated ISO dates and operational IDs stay
usable. Legacy indexes are refused until rebuilt with the privacy-policy marker.
Source files are not rewritten. Local runtime indexes were rebuilt with strict-v1.

Adds exact-source Hit@5 evaluation for every supplied query, with no oracle filters
and only the first five results eligible. Tests build fresh real-MiniLM collections,
report each hit/miss, and fail each template independently below 80%. Empty/missing
evaluation data fails; evidence from another template is an error.

Scope is only `part2_knowledge/`, with no dependency or shared-contract changes.
This is a rule-based boundary for tested formats/named fields, not universal PII
recognition or secure erasure of historical files/backups. Part 5's actual module
and real LLM providers remain separate work. The owner has explicitly confirmed
committing the implementation, creating this PR and merging it into main.

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
.\.venv\Scripts\python.exe -m pytest part2_knowledge/tests/test_search_quality.py -q
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

**144 Part 2 tests / 244 total tests passed.** Boundary tests inspect provider
arguments/schema examples, embedding inputs, persisted data and returned metadata.
They cover complete/partial formats, Unicode digits, short named private fields,
chunk-boundary leaks, masking/import failures, defaults/validators reintroducing
data, legacy-index rejection, and preservation of nonprivate codes/dates.

Quality-metric tests reject sixth-place hits, same filenames in other directories,
empty datasets and cross-template evidence, and verify the exact 80% threshold.
The real-model gate uses fresh temporary collections and all current cases:

| Attempt | Payments | University |
| --- | --- | --- |
| Existing ranking baseline | 12/12 (100%) | 12/12 (100%) |
| Strict privacy, unchanged ranking | 12/12 (100%) | 12/12 (100%) |

No tuning was necessary. The supplied sets are synthetic and small; these scores
do not establish general real-world accuracy. MiniLM must be cached/downloadable;
quality tests are not silently mocked or skipped. No external LLM call was made.

## Screenshots (for website changes)

Not applicable; this is Part 2 Python infrastructure.

## Contract changes?

- [x] No
- [ ] Yes – all five members must approve

Runtime copies of schema examples are sanitized; shared schema source files stay
unchanged. No issue is linked; teammate issue texts remain drafts in `CONTRACT_REVIEW.md`.
