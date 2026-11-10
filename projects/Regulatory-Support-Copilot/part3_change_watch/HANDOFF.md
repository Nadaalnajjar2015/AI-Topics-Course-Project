# Part 3 review and integration handoff — 2026-11-09

The authorized live follow-up, current metrics, failed attempts and safe local Git
commands are in [VERIFICATION.md](VERIFICATION.md). Its results supersede the
initial offline-only verification history retained below.

Khaled's assigned work is implemented locally on `khaledbranch`: a scoped GroqCloud
adapter in Part 2 plus the three Change Watch agents, CLI and quality tooling.
Nothing has been pushed and no PR has been opened. `main` was never checked out or
modified. HEAD remains `29e02529b02651c0a0f87298ba3ed1b3c7d50bbe`, equal to fetched
`origin/main` (0 ahead/0 behind); it is 3 ahead/0 behind `origin/khaledbranch`.

## Changed-file manifest

All paths below are relative to `projects/Regulatory-Support-Copilot/`.

| Path | Reason |
| --- | --- |
| `part2_knowledge/common/llm.py` | Route Groq through existing privacy boundary and public APIs; generic safe errors |
| `part2_knowledge/common/config.py` | Accept groq and a secret-hidden environment key, preserving defaults |
| `part2_knowledge/common/README.md` | Add Groq setup/mode/error/live-status guidance |
| `part2_knowledge/tests/test_groq.py` | Offline mocked SDK, routing, validation, redaction and failure tests |
| `requirements.txt` | Add only the authorized official groq SDK |
| `.env.example` | Empty Groq key and commented provider/model configuration |
| `contracts/schemas.py` | Authorized exception: six models in the designated Part 3 section only |
| `part3_change_watch/_support.py` | Private typed LLM schemas, prompt loading and citation safeguards |
| `part3_change_watch/watcher.py` | Numbered sections, extraction, quote/date verification and stable requirements |
| `part3_change_watch/impact.py` | RAG-backed unit choices, directory stakeholders, severity and unmatched IDs |
| `part3_change_watch/action_planner.py` | One validated pending-review draft per unit |
| `part3_change_watch/cli.py` | Typed pipeline and JSON CLI with explicit failure codes |
| `part3_change_watch/quality_check.py` | Eight real fixture cases, per-template and overall metrics; opt-in live evaluation |
| `part3_change_watch/live_smoke.py` | Opt-in two-call non-sensitive live smoke test |
| `part3_change_watch/live_verify.py` | Bounded live template smokes, provenance, checkpoints and eight-case evaluation |
| `part3_change_watch/prompts/watcher.md` | Watcher v1 prompt |
| `part3_change_watch/prompts/impact.md` | Impact v2: explicit source applicability controls unit scope |
| `part3_change_watch/prompts/action_planner.md` | Planner v2: complete requirement IDs and narrative coverage |
| `part3_change_watch/tests/conftest.py` | Explicit case-matched model and retrieval mocks |
| `part3_change_watch/tests/test_contracts.py` | All examples, descriptions, literal constraints and JSON round-trips |
| `part3_change_watch/tests/test_watcher.py` | Quotes, sections, metadata/background, dates and source injection |
| `part3_change_watch/tests/test_pipeline.py` | Both templates, stakeholders, evidence, actions, CLI, metrics and real retrieval with mocked LLM |
| `part3_change_watch/tests/test_live_verify.py` | Offline live-permission, smoke gates, pacing and retry/call-budget checks |
| `part3_change_watch/README.md` | Setup, architecture, responsibilities, prompt history and limitations |
| `part3_change_watch/AI_LOG.md` | Actual Codex decisions and verification history |
| `part3_change_watch/HANDOFF.md` | This manifest, integration example, reviewer notes and issue/PR drafts |
| `part3_change_watch/VERIFICATION.md` | Current real-model verification, metric definitions and safe local commands |

Part 1, Part 4, Part 5, fixtures, root/project README, privacy implementation,
prompt renderer, RAG ingestion/search/ranking and `.github` were not edited.
The pre-existing root `.vscode/settings.json` was left untouched and unstaged.
Runtime indexes were rebuilt using the existing public ingest command and remain
ignored. `.env`, keys, `.venv`, indexes and runtime state are not staged.

## Rawan / Part 4

Use the exact public signatures; the same calls work for either explicit template:

```python
from part1_templates.tools.changes import get_change
from part3_change_watch.watcher import summarize
from part3_change_watch.impact import analyze
from part3_change_watch.action_planner import plan

doc = get_change("CHG-U-001", template_id="university")
summary = summarize(doc)
report = analyze(summary)
actions = plan(summary, report)
outputs = {
    "summary": summary.model_dump(mode="json"),
    "impact_report": report.model_dump(mode="json"),
    "action_items": [item.model_dump(mode="json") for item in actions],
}
```

Run steps in order: Change Watcher, Impact Analyst, Action Planner. Store each output
under the above keys and mark the finished task pending_review. Propagate a failed
step to a readable failed task; do not silently substitute fake results or retry
semantic failures. An empty requirement list is valid and yields no actions.
Missing indexes name the existing ingestion command. If due_before is required but
the source has no date, the planner raises a clear human-input error. Part 3 never
calls `create_action_item`; approval and persistence belong to the reviewed workflow.

## Nada / Part 5

Display original title/scope/effective date, each requirement's source_quote and
source_location, and the impact sources' source/location/score/metadata intact.
Similarity score is retrieval relevance, not confidence or correctness. Use the
task's explicit template for labels and data isolation. Render model/source text as
escaped text, never trusted HTML. Actions have stable IDs, scoped stakeholder IDs,
an owner role, source due date, 2–4 checks and pending_review status. Only a human
decision may approve/reject and subsequently save an action. Unknown-date drafts
requiring a deadline need a reviewer input path. A fake-provider run must be visibly
labelled interface-only; the watcher intentionally returns no mock requirements.

## Khadija review: isolated cross-owner Part 2 change

Review all six adapter-related files in the first six manifest rows. Existing fake,
privacy, configuration and search tests were left intact. `privacy.py`, prompting,
search, ingestion, ranking, Chroma settings and source fixtures were not changed.
The adapter preserves masking of both prompt strings, sanitized schema/example
payloads, real provider output and post-validation output. Reintroduced private data
still raises PrivacyError. API exception bodies and headers never reach error text.
No real-provider failure falls back to fake. Empty/refused/truncated responses,
invalid JSON, contract failures, absent credentials, 401/403/429, transport failures
and unsupported models/schemas fail explicitly. SDK timeout/retries use settings.

The adapter selects strict mode only for documented supporting models and closed,
fully required schemas. Existing optional/open schemas retain best-effort mode.
Other models use JSON-object mode with an explicit schema. Review the capability
list against current official docs before a live run. SDK 1.7.0 and real Groq calls
were verified in the follow-up; mocked SDK tests remain a separate result category.
No adapter call can mutate the knowledge base; existing
real MiniLM retrieval-quality gates still pass independently for both templates.

## Shared contracts — Contract changes: YES

Requirement, ChangeSummary, Impact, ImpactReport, Check and ActionItem were added
only between the existing Part 3/Part 4 markers. No Part 1/2 model or import was
edited. Every field has a description, nested models use Pydantic v2, dates remain
date/null, and status/category/severity have literal constraints. All examples
validate and JSON-round-trip. ActionItem permits historical reviewed states and
one-check history fixtures, while the planner enforces 2–4 checks on new drafts.

**All five team members must approve these shared additions before merging.**
Khadija's cross-owner review is a separate requirement. No approval to merge is
implied by authorization to implement on khaledbranch.

## Initial offline verification history and current follow-up

Current follow-up commands passed 183 Part 2 tests, 107 Part 3 tests and 390 total
tests, with no failed/skipped tests. Both template search gates remain 12/12.
Both templates have completed real smoke cases; the eight-case real-model results
and any incomplete/failed attempts are documented in VERIFICATION.md. The original
offline run details below are historical, not the current SDK/live-test status.
The fresh 120B evaluation completed 5 Payments and 3 University cases, with all
reported fixture metrics at 100% per template. It produced 24 verified quotations
and 14 pending actions. Thirteen of 41 impacts lack retrieved supporting passages
and are capped low; human review remains necessary. The quota-blocked 20B run is
reported separately and is not combined with those complete results.

Commands ran from the Python project folder with its existing Windows `.venv`.
Activate it first to use the equivalent `python -m ...` commands below.

| Actual command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest part2_knowledge/tests/test_groq.py part2_knowledge/tests/test_llm.py -q` | 52 passed |
| `.\.venv\Scripts\python.exe -m pytest part2_knowledge/tests -q` | 179 passed, 0 failed/skipped |
| `.\.venv\Scripts\python.exe -m pytest part3_change_watch/tests -q` | 96 passed, 0 failed/skipped; the initial run had one incorrect test line-number expectation, which was corrected |
| `.\.venv\Scripts\python.exe -m pytest -q` | 375 passed, 0 failed/skipped, including the two added tests |
| `.\.venv\Scripts\python.exe -m part2_knowledge.knowledge_base.ingest` | Payments 15 files/89 chunks; university 15 files/63 chunks |
| `.\.venv\Scripts\python.exe -m part3_change_watch.cli CHG-P-002` | Exit 0, fake warning, correctly identified payments JSON, no requirements/actions |
| `.\.venv\Scripts\python.exe -m part3_change_watch.cli CHG-U-001 --template university` | Exit 0, fake warning, university JSON, no requirements/actions |
| `.\.venv\Scripts\python.exe -m part3_change_watch.quality_check` | Exit 0 for interface execution only; eight cases, targets_met=false |

One repeated full-suite run had 374 passes and one failure in the unchanged
`part2_knowledge/tests/test_ingest.py::test_ingest_all_sources_rebuilds_stable_isolated_cosine_collections`:
Chroma reported `Error creating hnsw segment reader: Nothing found on disk`.
The exact isolated test then passed (1 passed), and the final full suite passed
375/375 in 15.75 seconds. This intermittent storage-test failure is disclosed;
its root cause was not established and no Part 2 ingestion or existing test was
changed to suppress it. Khadija should investigate if it recurs.

The unchanged Part 2 real MiniLM gate measured payments Hit@5=12/12 and university
Hit@5=12/12 on fresh temporary indexes. Pipeline tests use case-matched model mocks,
including an eight-case metric computation and two real-Chroma/mocked-LLM runs.
Expected payments ACH/IPS groups are BANK-A/B/E; computing internship groups include
STU-CS-2026, STU-SE-2026 and STU-INTL through the directory. These model mocks do
not establish live extraction or regulatory accuracy. The unmocked fake evaluation
returns zero requirements/impacts/actions, so semantic targets are not met.

At the initial offline delivery: **LIVE GROQ TEST NOT RUN. LIVE GROQ QUALITY EVALUATION NOT RUN.** A configured local
key was detected as a boolean only. The Groq SDK is absent; its installation failed
with sandbox socket denial. No elevation outside the authorized fetch was requested.
Live calls also require explicit authorization, which was not granted in this task.
Those SDK/authorization blockers were resolved for the follow-up. For a separately
authorized local rerun, use the current bounded commands in VERIFICATION.md or:

```powershell
.\.venv\Scripts\python.exe -m pip install groq
# In ignored .env: LLM_PROVIDER=groq, LLM_MODEL=openai/gpt-oss-20b, your local key.
.\.venv\Scripts\python.exe -m part3_change_watch.live_smoke --allow-live
.\.venv\Scripts\python.exe -m part3_change_watch.quality_check --allow-live --interval 3
```

The quality command runs its own two-call smoke first, then sequential cases with
bounded SDK retries and pauses. A successful two-call smoke is not an accuracy
measurement. Review real results and failures before selecting a production demo.
Quote repairs are deliberately conservative; missed requirements and unsupported
source layouts need real-model review. Watcher remains v1; impact and planner v2
address observed applicability/requirement-ID problems. See the measured results;
neither schema validity nor these synthetic fixtures guarantees regulatory accuracy.

## Local commits and publication

No new commit could be created: normal `git add` failed creating `.git/index.lock`
because sandbox Git metadata is read-only. Nothing is staged. Fetch and later bounded
live commands received command-specific permission; staging/commit elevation was
not requested. Git permissions were not changed. No push or PR is authorized. Suggested separate commits when running
Git in a permitted local terminal, always verifying branch before/after operations:

1. `feat(part2): add groq provider through llm wrapper` — first six manifest rows.
2. `feat(part3): add change watch contracts` — only contracts/schemas.py, with all-five review notice.
3. `feat(part3): implement verified change watch pipeline` — agents, helpers, prompts, CLI, smoke/quality scripts.
4. `test(part3): cover both templates and failure safeguards` — Part 3 tests.
5. `docs(part3): document setup and integration handoff` — Part 3 documentation.

Never stage `.vscode/`, `.env`, `.venv` or runtime data. Publishing requires the
user's separate explicit approval; do not create or merge a PR automatically.

## Copy-ready PR draft (not published)

Title: `feat(part3): add verified change watch pipeline and scoped Groq adapter`

### What this PR does

New changes can now flow through source-verified requirement extraction, template-
isolated impact analysis and one pending-review action per affected unit. Adds
GroqCloud through Part 2's existing privacy-preserving LLM APIs and six agreed
Part 3 contract models. No action is sent, approved or saved by an agent.

### Which part

- [x] Part 2 — cross-owner adapter change: Khadija review required
- [x] Part 3
- [ ] Part 1
- [ ] Part 4
- [ ] Part 5

### How I tested it

390 tests passed, no failed/skipped tests. Includes existing Part 1/2 regression
tests, mocked Groq SDK, both-template pipeline safeguards and actual MiniLM search
gates (12/12 per template). Both fake CLIs and the interface runner execute.
SDK 1.7.0 and authorized real Groq smoke calls were verified; VERIFICATION.md records
the actual eight-case results and failed attempts. No semantic accuracy claim is
based on mocks/fake outputs. Closed private response models use guarded strict
output; optional/open contracts remain backward-compatible.
The complete 120B run met all reported targets for both templates; requirement
recall uses the supplied minimum counts. Thirteen evidence gaps remain low severity.

### Screenshots

Not applicable: no website changes.

### Contract changes?

- [ ] No
- [x] Yes — all five members must approve

No issue number is invented. Local commits/publication remain pending Git permission
and explicit user approval for any push/PR.

## Copy-ready issues (not posted)

**All owners — Review Part 3 shared contracts**  
Labels: contract, part-3. Review the six additions in contracts/schemas.py against
Project Guide 8.1 and Part 1 historical actions. Every model example validates;
Part 1/2 definitions are preserved. Obtain all five approvals before merging.

**Rawan — Connect Change Watch agents to task orchestration**  
Labels: part-4, integration. The orchestrator package is still a placeholder.
Implement the three sequential steps using the public example above; store JSON
under summary, impact_report and action_items. Add failed-step handling, pending
review state and per-template integration tests. Do not persist unapproved actions.

**Nada — Implement reviewed Change Watch UI and actual safety/audit modules**  
Labels: part-5, integration. The website and actual masking/audit modules are absent.
Display quotes/citations and pending actions using template labels. Escape source
text and require human review before Part 1 persistence. Verify the actual masking
hook against the unchanged strict Part 2 boundary. Preserve visible fake/live labels.

**Repository owner — Verify main protection and replace owner placeholders**  
Labels: question. The original audit reported main protection OFF; this session did
not independently inspect current GitHub protection settings. Please verify and
enable the agreed PR/approval controls. CODEOWNERS still contains @member2,
@member3 and @member4. Replace these separately; no settings or CODEOWNERS were
changed by this implementation. Shared contracts still require all five approvals.

No new Zain/Part 1 blocker was found; its public directory/storage interfaces work
with these contracts and all existing Part 1 tests pass.

## موجز الفريق

نفّذ خالد وكلاء Change Watch الثلاثة وواجهة سطر الأوامر على khaledbranch.
تستخرج السلسلة المتطلبات وتتحقق من الاقتباسات، ثم تحدد الوحدات والفئات المتأثرة وتكتب مسودات الإجراءات.
أُضيف دعم Groq عبر واجهة الجزء الثاني مع الإبقاء على حماية الخصوصية.
نجح 390 اختباراً، ونجحت تجارب Groq الحية للقالبين، وتفاصيل التقييم الحقيقي في VERIFICATION.md.
تحتاج روان إلى ربط الدوال الثلاث بمنسق المهام، وتحتاج ندى إلى عرض المصادر ومسار المراجعة البشرية.
يلزم أن تراجع خديجة تعديلات الجزء الثاني وأن يوافق الأعضاء الخمسة على العقود المشتركة قبل الدمج.
لم يُعدّل main، ولم تُنشر التغييرات أو يُفتح طلب دمج، وتعذرت الالتزامات المحلية بسبب صلاحيات بيئة التنفيذ.
