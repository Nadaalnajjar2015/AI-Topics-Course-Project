# Live verification — 2026-11-09

This report supersedes the initial offline-only status in HANDOFF.md. Live calls
were explicitly authorized in the follow-up. No credentials, .env contents or SDK
error bodies are included here. Raw sanitized pipeline outputs and attempt logs
are saved under ignored `runtime/part3_live/`, outside Part 1 action storage.

## Environment and model

- Existing virtual environment: `.venv`, Groq SDK 1.7.0.
- Persistent settings remain `fake` / `qwen2.5:7b`; that is an Ollama model setting,
  not a Groq model. Verification overrides only its own process to `groq` /
  `openai/gpt-oss-20b`; the local .env remains untouched.
- The official [Groq structured-output documentation](https://console.groq.com/docs/structured-outputs)
  lists this model for strict and best-effort JSON Schema modes. Real API acceptance
  and local Pydantic validation, rather than the model list alone, verify this run.
- Closed, fully required Part 3 response schemas use `strict=true`. Open schemas,
  schemas with defaults or nested free metadata use best-effort mode; models without
  documented strict support cannot enter strict mode. Other models retain JSON-object
  mode. The fake branch and all existing privacy checks remain in effect unchanged.
- The 20B daily quota later stopped the full evaluation. A fresh, separately
  identified run uses `openai/gpt-oss-120b`, also documented for strict output.
  Model selection is explicit in the test command; the production adapter does
  not silently switch models or providers on failure.

## Observed issues and fixes

1. The first sandboxed request failed at transport. The authorized live commands
   were retried with permission limited to those bounded commands; no unrestricted
   permission, Git write elevation or global settings change was requested.
2. Initial best-effort template smokes completed. Payments found the correct three
   requirements but added a false-positive unit based on shared technical terminology
   (unit precision 2/3); University matched both units. Both had valid quotes and
   exact stakeholder sets. These results are retained as baseline artifacts.
3. Impact prompt v2 makes the source's explicit applicability boundary authoritative
   and excludes speculative indirect effects. It contains no template-specific IDs
   or evaluation answers. The corrected Payments smoke returned only its two intended
   units, with three verified requirements and two pending-review actions.
4. A first best-effort evaluation stopped on HTTP 400 at impact selection. The
   public adapter's error was deliberately generic, so the precise provider reason
   is unconfirmed. Best-effort schema generation can produce such failures according
   to Groq's documentation. Private Part 3 schemas now forbid extra fields; guarded
   strict routing was added only to the new Groq adapter. The strict retest accepted
   all three private response model types. No semantic failure is automatically
   retried or replaced with fake data.
5. Planner prompts previously repeated citations across impacts. They now send one
   deduplicated evidence list and separate impact facts. Final ActionItem citations
   remain unchanged, with every original citation field preserved.
6. A strict University run passed schema validation but failed a later pipeline
   check. Its precise validation reason was not captured in that first attempt.
   Planner v2 clarifies complete, separate requirement IDs; a six-call University
   retest completed successfully. Validation was not weakened. Later runner attempts
   capture already-sanitized validated responses and safe validation reasons.
7. The final 20B attempt exhausted rate-limit retries while planning the fifth case.
   A small probe succeeded, but a bounded resume received a daily-quota rejection.
   A safe diagnostic recorded only HTTP 429, daily scope and a numeric retry delay;
   no raw provider body, account identity or credential was printed. Further 20B
   retries stopped immediately. Its completed four-case result remains archived.

The runner spaces calls 25 seconds apart, adds at most two 30-second outer retries
only for explicit rate limits, and caps wrapper attempts. The SDK has one configured
transport retry per wrapper call. Therefore wrapper counts are not HTTP-attempt or
token-usage counts. No exact token consumption or account quota is claimed.

## Final real-model results

The final 120B run is complete; both template targets were met. The partial 20B run remains separate.
The source fixtures provide minimum requirement counts, not exhaustive gold semantic
labels. Requirement recall is therefore the documented capped count/minimum proxy;
it is accompanied by counts and source-quote checks, not presented as independently
annotated semantic recall. Unit metrics use exact sets; stakeholder accuracy is the
fraction of cases with an exact expected set. Template results are macro averages.
Key facts are checked in generated narratives and the effective date; copied quotes
and retrieved text cannot satisfy this metric alone. All are synthetic fixtures.

### Completed GPT-OSS 120B run — all eight cases

Model: `openai/gpt-oss-120b`; SDK: 1.7.0; private response mode: JSON Schema
`strict=true`. Both same-model template smokes passed (12 successful calls), then
the complete evaluation made 46 successful wrapper calls with zero outer retries,
zero wrapper failures and no fake/model-mock outputs. SDK internal transport retries
are not separately instrumented.

| Template | Cases | Requirements/minimum | Minimum-count recall | Unit precision | Unit recall | Exact stakeholders | Quote validity | Literal key facts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Payments | 5 | 15/15 | 100% | 100% | 100% | 100% | 100% | 100% |
| University | 3 | 9/9 | 100% | 100% | 100% | 100% | 100% | 100% |

| Case | Requirements/minimum | Unit precision | Unit recall | Exact stakeholders | Quotes | Key facts |
| --- | --- | --- | --- | --- | --- | --- |
| CHG-P-001 | 3/3 | 100% | 100% | Yes | 100% | 100% |
| CHG-P-002 | 3/3 | 100% | 100% | Yes | 100% | 100% |
| CHG-P-003 | 3/3 | 100% | 100% | Yes | 100% | 100% |
| CHG-P-004 | 3/3 | 100% | 100% | Yes | 100% | 100% |
| CHG-P-005 | 3/3 | 100% | 100% | Yes | 100% | 100% |
| CHG-U-001 | 3/3 | 100% | 100% | Yes | 100% | 100% |
| CHG-U-002 | 3/3 | 100% | 100% | Yes | 100% | 100% |
| CHG-U-003 | 3/3 | 100% | 100% | Yes | 100% | 100% |

The saved-output audit validated 24 source quotations and 14 pending-review actions
across all eight cases. It found 41 impacts, **13 without supporting retrieved
passages**, and zero unmatched requirements. Evidence gaps retain low severity and
an explicit explanation. Every action has the exact directory stakeholders, source
effective date, all requirement IDs supplied by its impacts and 2–4 checks. This
checks actual saved real-model outputs, independently of the mocked tests.

The supplied answer sets evaluate case-level unit unions and minimum requirement
counts; they do not exhaustively annotate each requirement-to-unit mapping. These
are one-pass results on eight small synthetic fixtures, not a production regulatory-
correctness guarantee. Narrative completeness, citations and check assumptions still
require human review.

Current artifacts (local, ignored; never staged):

- `runtime/part3_live/evaluation.json`: complete 120B metrics, outputs, validated responses, prompt versions and implementation hashes.
- `runtime/part3_live/smoke.json`: both successful 120B template smoke cases.
- `runtime/part3_live/output-audit.json`: independent saved-output invariant checks.
- `runtime/part3_live/evaluation-20b-partial.json`: the separate quota-blocked 20B run.
- `runtime/part3_live/wrapper-smoke.json`: successful ordinary-text/JSON wrapper smoke on 20B.
- Earlier stopped/baseline attempts are retained under distinct filenames.

### Offline regression results

Executed from the project folder with the existing virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pytest part2_knowledge/tests -q
.\.venv\Scripts\python.exe -m pytest part3_change_watch/tests -q
.\.venv\Scripts\python.exe -m pytest -q
```

Results: **183 passed**, **107 passed**, and **390 passed**, respectively; zero
failed/skipped tests in these final runs. Existing real MiniLM search-quality gates
stayed 12/12 for each template. Mock SDK/LLM tests are separate from the live
measurements above. The earlier delivery's intermittent Chroma failure remains
recorded in HANDOFF.md; it did not recur in these final runs.

### Archived 20B partial run — not an eight-case result

`evaluation-20b-partial.json` contains 4/8 completed cases: Payments 4/5 and
University 0/3. University smoke output is a separate test and is not counted as
an evaluation case. The incomplete fifth case is not fabricated or counted as a
successful result. This phase made 31 wrapper attempts including the stopped resume.

| Completed case | Requirements/minimum | Unit precision | Unit recall | Exact stakeholders | Quotes | Literal key facts |
| --- | --- | --- | --- | --- | --- | --- |
| CHG-P-001 | 3/3 | 100% | 100% | Yes | 100% | 100% |
| CHG-P-002 | 3/3 | 100% | 100% | Yes | 100% | 100% |
| CHG-P-003 | 3/3 | 100% | 100% | Yes | 100% | 100% |
| CHG-P-004 | 3/3 | 100% | 100% | Yes | 100% | 66.7% |

The wallet result used U+2010 in `basic‐KYC`, while the supplied key fact uses an
ASCII hyphen in `basic-KYC`. The other two key facts, `500` and `AG01`, are present.
The frozen literal scorer was not altered to raise the score: its observed
Payments-subset mean remains 91.7%. This is not full-template or semantic accuracy.
Numerical checks also need human review of starting state and the quantity being
limited; a valid JSON draft is not proof that its operational checks are sufficient.

## Reproduce without changing .env

From the project folder, after reviewing the live authorization and rate budget:

```powershell
.\.venv\Scripts\python.exe -m part3_change_watch.live_verify --allow-live --phase smoke --model openai/gpt-oss-120b --interval 25 --max-calls 16
.\.venv\Scripts\python.exe -m part3_change_watch.live_verify --allow-live --phase evaluation --model openai/gpt-oss-120b --interval 25 --max-calls 55
```

The evaluation phase requires a completed same-model two-template smoke report.
`--resume` reuses completed cases only when model, prompts and implementation hashes
match, within the same total attempt budget. Reports include prompt versions and
implementation hashes. Runtime reports are never staged. Tests never invoke live
requests automatically.

## Safe local review and commits

Git staging was previously denied by read-only sandbox Git metadata. It was not
retried with elevated Git permissions. No commit, push or PR has been created.
The following commands are for the owner to run locally, one reviewed block at a
time, from `projects/Regulatory-Support-Copilot/`. They name implementation files
explicitly and do not stage .env, .vscode, .venv or runtime reports.

```powershell
function Invoke-KhaledGit {
    param([string[]]$GitArguments)
    if ((git branch --show-current) -ne 'khaledbranch') { throw 'Expected khaledbranch; stopped.' }
    & git @GitArguments
    $taskGitExit = $LASTEXITCODE
    if ((git branch --show-current) -ne 'khaledbranch') { throw 'Branch changed; stopped.' }
    if ($taskGitExit -ne 0) { throw 'Git command failed; no further operation is authorized.' }
}
# Start with an empty index; inspect any existing staged work separately.
Invoke-KhaledGit -GitArguments @('diff', '--cached', '--quiet')
Invoke-KhaledGit -GitArguments @('diff', '--check')
```

Review and commit the isolated Groq change first:

```powershell
$taskGroqFiles = @(
  'part2_knowledge/common/llm.py', 'part2_knowledge/common/config.py',
  'part2_knowledge/common/README.md', 'part2_knowledge/tests/test_groq.py',
  'requirements.txt', '.env.example'
)
Invoke-KhaledGit -GitArguments (@('add', '--') + $taskGroqFiles)
Invoke-KhaledGit -GitArguments @('diff', '--cached', '--name-only')
Invoke-KhaledGit -GitArguments @('diff', '--cached', '--check')
# After reviewing those exact staged paths:
Invoke-KhaledGit -GitArguments @('commit', '-m', 'feat(part2): add groq provider through llm wrapper')
```

Keep shared contracts in a separate commit. All five members must approve before merge:

```powershell
Invoke-KhaledGit -GitArguments @('add', '--', 'contracts/schemas.py')
Invoke-KhaledGit -GitArguments @('diff', '--cached', '--name-only')
Invoke-KhaledGit -GitArguments @('diff', '--cached', '--check')
Invoke-KhaledGit -GitArguments @('commit', '-m', 'feat(part3): add change watch contracts')
```

Then review and commit only these Part 3 paths:

```powershell
$taskPart3Files = @(
  'part3_change_watch/_support.py', 'part3_change_watch/watcher.py',
  'part3_change_watch/impact.py', 'part3_change_watch/action_planner.py',
  'part3_change_watch/cli.py', 'part3_change_watch/quality_check.py',
  'part3_change_watch/live_smoke.py', 'part3_change_watch/live_verify.py',
  'part3_change_watch/prompts/watcher.md', 'part3_change_watch/prompts/impact.md',
  'part3_change_watch/prompts/action_planner.md', 'part3_change_watch/tests/conftest.py',
  'part3_change_watch/tests/test_contracts.py', 'part3_change_watch/tests/test_watcher.py',
  'part3_change_watch/tests/test_pipeline.py', 'part3_change_watch/tests/test_live_verify.py',
  'part3_change_watch/README.md', 'part3_change_watch/HANDOFF.md',
  'part3_change_watch/AI_LOG.md', 'part3_change_watch/VERIFICATION.md'
)
Invoke-KhaledGit -GitArguments (@('add', '--') + $taskPart3Files)
Invoke-KhaledGit -GitArguments @('diff', '--cached', '--name-only')
Invoke-KhaledGit -GitArguments @('diff', '--cached', '--check')
Invoke-KhaledGit -GitArguments @('commit', '-m', 'feat(part3): implement and verify change watch pipeline')
```

Khadija must review the Part 2 changes, including guarded strict selection. All five
members must approve the shared contracts. No push, PR creation or merge is included
or authorized. Rawan still needs the task orchestrator; Nada still needs the website,
actual safety/audit hooks and reviewed persistence. Part 3 never approves or sends.
