# Part 5: Website, Safety and Evaluation

**Owner:** Nada Alnajjar (Nadaalnajjar2015)
**Guide:** `docs/05-Part5-Website-Safety-and-Evaluation.pdf`

The demo website (template switcher, live task page, human review), the safety layer
(masking, audit log, approval rule, guidelines) and the per-template evaluation.

```
part5_web/
  app.py          FastAPI app: routers, error pages, input validation (400/404)
  pages.py        HTML pages (Dashboard, New Change, Requests, Task, Action Items, Audit, Search, Setup, Evaluation)
  api.py          JSON API (/api/...), used by the page JavaScript and tests
  review.py       Approve / Edit / Reject rules; closes the task when every item is decided
  context.py      active template (query → cookie → ACTIVE_TEMPLATE), reviewer picker, lookups
  templates/      Jinja2 HTML (every organization word comes from template.labels)
  static/         style.css, task.js (polling every 2 s while running, review buttons)
  safety/         masking.py, audit.py, guidelines.md
  evaluation/     run_eval.py, report.py
  tests/
```

## Run

From `projects/Regulatory-Support-Copilot/`:

```powershell
python -m part2_knowledge.knowledge_base.ingest     # once: build the search index
uvicorn part5_web.app:app --reload                  # http://127.0.0.1:8000
python -m part5_web.evaluation.run_eval --template all   # also --only changes|requests|search, --limit N
python -m pytest part5_web/tests tests/integration -q
```

## Public functions

| Function | Used by |
| --- | --- |
| `safety.masking.mask(text) -> str` | Part 2 `privacy.mask_text()` → every LLM call |
| `safety.masking.find_leaks(text) -> dict` | evaluation and tests |
| `safety.audit.log_event(actor, action, task_id, details, template_id=None)` | Part 4 orchestrator, the website; never raises |
| `safety.audit.list_events(task_id=None, template_id=None)` | Audit Log page, `/api/audit` |
| `safety.audit.save_decision(decision)`, `list_decisions(task_id)` | review logic |

Audit events and review decisions live in the same SQLite file as Part 4's tasks
(`APP_DB`, default `runtime/app.db`). Audit events are append-only (database triggers
refuse UPDATE and DELETE). Contract models `ReviewDecision` and `AuditEvent` are in
`contracts/schemas.py`.

## Review rules (Guide 5.4)

| Action | Effect | Audit |
| --- | --- | --- |
| Approve action item | status approved, `update_output()`, `create_action_item()` | `action_item_approved` |
| Edit action item | new description/checks saved, then approved | `action_item_edited` |
| Reject | comment required | `action_item_rejected` / `reply_rejected` |
| Approve reply | `set_request_status(id, "answered")` (mock: nothing is sent) | `reply_sent` |
| Edit reply | new reply saved, then answered | `reply_edited`, `reply_sent` |
| All items decided | task `approved` if anything approved, else `rejected` | `task_approved` / `task_rejected` |

A change task with no action items (for example with the fake provider) can be closed by the
reviewer with one decision on the change itself.

## Masking

| Data | In | Out |
| --- | --- | --- |
| IBAN | `JO71 CBJO 0010 0000 0000 0131 0003 02` | `JO71 **** **** 02` |
| Account number (10–18 digits) | `0013100030212` | `*********0212` |
| Card | `4111 1111 1111 1111` | `**** **** **** 1111` |
| National ID | `9881023456` | `******3456` |
| Phone | `+962 79 123 4567` | `+962 ** *** 4567` |
| Email | `ops@northfield-bank.example` | `o***@northfield-bank.example` |

Kept unchanged: `BANK-C`, `S-2291`, `7731`, `SE301`, request IDs, reason codes, dates.
Part 2 already redacts these values fully before calling `mask()`, so model prompts contain
`[REDACTED]`; `mask()` is the human-readable version used for pages and audit details.

## Deploy (free, Render)

`render.yaml` (project folder) describes one free Render web service: build = install + build the
search index, start = `python -m part5_web.serve` (rebuilds a missing index in a child process,
then serves on `$PORT`), health check `/healthz`, auto-deploy on every push to the chosen branch.

Secrets are set only in the Render dashboard, never in Git: `GROQ_API_KEY` and `SITE_PASSWORD`
(optional browser password for the public site; any username works; `/healthz` stays open).

Free-plan limits: 512 MB RAM (the app uses about 260 MB), sleeps after 15 min without traffic
(first visit then takes about a minute), and the SQLite database (tasks, decisions, audit log)
resets on every restart or deploy because the free disk is not persistent.

## Known limits

- The reviewer picker is not real login.
- With `LLM_PROVIDER=fake` Change Watch extracts no requirements; use the demo model (Groq) for Demo A.
- The evaluation report in `docs/evaluation-report.md` is currently from the **fake** provider; re-run it with the demo model.
