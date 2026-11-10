# Part 3: Change Watch Agents

Owner: Khaled. Same typed Python pipeline for both organization templates:

```text
ChangeDocument -> summarize -> ChangeSummary -> analyze -> ImpactReport
                                  |                         |
                                  +-------- plan -----------+ -> list[ActionItem] -> human review
```

Public APIs: `watcher.summarize(doc: ChangeDocument) -> ChangeSummary`,
`impact.analyze(summary: ChangeSummary) -> ImpactReport`, and
`action_planner.plan(summary: ChangeSummary, report: ImpactReport) -> list[ActionItem]`.

The LLM extracts requirements, selects units from actual candidates, and writes
draft narratives. Code preserves identity/scope, splits numbered source sections,
verifies exact quotes (only conservative punctuation/case repair), verifies dates,
rejects foreign units/citations, derives stakeholders through Part 1, computes
severity, groups one action per unit and assigns stable IDs. Search uses explicit
template IDs and document-type filters; original citations retain all their fields.
Source instructions are untrusted user data, JSON-escaped inside document tags.
No agent approves, sends or saves actions. Every output action is `pending_review`.

Mandatory changes already effective or within 90 days are high; later or unknown
dates are medium; optional changes are low. A reasoned LLM escalation is limited to
one level. Missing evidence always caps severity at low. Unknown effective dates
remain null in summaries; if a template requires a filled `due_before`, planning
raises an actionable error instead of inventing a deadline. Extraction currently
accepts source quotes only from numbered sections, excluding front matter and
background headings. Summary/narrative correctness still requires human review.

From `projects/Regulatory-Support-Copilot/`, activate `.venv` (or prefix commands
with `.\.venv\Scripts\python.exe` in place of `python`), then:

```powershell
python -m pip install -r requirements.txt
python -m part2_knowledge.knowledge_base.ingest
python -m part3_change_watch.cli CHG-P-002
python -m part3_change_watch.cli CHG-U-001 --template university
python -m pytest part2_knowledge/tests -q
python -m pytest part3_change_watch/tests -q
python -m pytest -q
python -m part3_change_watch.quality_check
```

CLI stdout is one readable JSON object containing `summary`, `impact_report`,
`action_items`, `provider` and `interface_only`. Exit codes: 0 success, 2 invalid
input/draft, 3 provider/privacy/index failure. Fake mode emits an explicit warning
to stderr and returns zero extracted requirements: it cannot simulate a successful
production demo. The eight-case quality runner reports minimum requirement counts,
unit precision/recall, exact stakeholders, quote validity and narrative key-fact
coverage per case/template/overall. Empty requirement lists score quote validity 0.
Copied retrieval passages/quotes cannot satisfy narrative key-fact coverage.

For Groq, configure only your ignored `.env`: `LLM_PROVIDER=groq`,
`LLM_MODEL=openai/gpt-oss-20b`, and your local `GROQ_API_KEY`. No key belongs in chat.
The shared Part 2 wrapper handles all calls and strict redaction. Closed, fully
required response schemas use strict mode on documented supporting models; other
schemas retain best-effort mode. All JSON still undergoes Pydantic validation. See
[Part 2 setup and official references](../part2_knowledge/common/README.md).
After explicit authorization for real calls, run:

```powershell
python -m part3_change_watch.live_smoke --allow-live
python -m part3_change_watch.quality_check --allow-live --interval 3
python -m part3_change_watch.live_verify --allow-live --phase smoke --interval 25 --max-calls 18
python -m part3_change_watch.live_verify --allow-live --phase evaluation --interval 25 --max-calls 65
```

The quality command first runs a two-call non-sensitive smoke test, then processes
all eight cases sequentially. It pauses between calls; increase `--interval` for
your account limits. SDK retries are bounded by `LLM_MAX_RETRIES`; quota exhaustion
stops the run. The explicit live flag is never added by pytest/CI.
`live_verify` instead overrides only its own process to Groq/model settings,
requires completed Payments and University pipeline smokes before evaluation,
preserves sanitized outputs and attempt logs in ignored runtime storage, and
supports `--resume` for stopped same-code evaluations. It retries only explicit
rate limits within a total call budget. `--smoke-template university` or `payments`
retests one failed smoke without repeating another case that already completed.

Validation on 2026-11-09: all offline tests and both template search-quality gates
passed (details in [HANDOFF.md](HANDOFF.md)). Case-matched mocks verify pipeline
safeguards across eight fixtures; they are not regulatory accuracy measurements.
Fake CLI runs succeeded for payments and university with empty interface outputs.
The initial offline-only delivery had no installed Groq SDK or live authorization.
The authorized follow-up verified SDK 1.7.0 and real Groq responses. Current live
results, stopped attempts, remaining limits and safe local Git commands are in
[VERIFICATION.md](VERIFICATION.md); mocked results never stand in for those results.
The completed 120B live run passed all eight fixture cases: 15/15 minimum
requirements for Payments and 9/9 for University, with 100% reported unit,
stakeholder, quote and literal key-fact metrics for each template. The audit found
13 impacts without retrieved supporting passages; those remain low severity.
The fixture metrics do not establish production correctness or exhaustive
requirement-to-unit mapping accuracy. All 14 output actions remain pending review.

Prompt history: v1 (2026-11-09) introduced the three versioned prompt files, template
labels, strict source/evidence instructions and narrative-only planning. Impact v2
reinforces source applicability after a real false-positive unit selection; planner
v2 requests every complete requirement ID separately. Provider/schema hardening
and deduplicated prompt evidence are recorded separately from semantic results.

Review before merge: Khadija approves the isolated Part 2 adapter changes; all five
members approve the six shared contract additions. [HANDOFF.md](HANDOFF.md) includes
Part 4/5 call examples, review notes and copy-ready issue texts.
