# Contracts

Plain-language description of every model in `schemas.py` and every public function each part exposes.
Full tables: `docs/00-Project-Guide.pdf`, Section 8. Keep this file in sync with `schemas.py`.

**Golden rule:** no organization-specific words in contracts (no `student_id`, `course`, `patient`).
The code uses general words; each template's `labels` turn them into the organization's words.
Examples in `schemas.py` use university data.

## Data models

### Part 1 – Templates, Mock Data and Connectors

- **TemplateConfig** – one organization's settings from `template.yaml`: id, organization name, languages,
  labels (the organization's words), which connector reads its records, the regex that finds an item in a
  request, the reason-codes document, prompt hints, action-item fields and reviewer roles.
- **Unit** – a part of the organization a rule can affect (study program, office, department).
- **Stakeholder** – a group of people a rule can affect (student group, patient group, staff group), with the
  units it belongs to and extra attributes (for example `international: true`).
- **ChangeDocument** – a new rule or policy to analyze: id, template, title, issuer, scope, published and
  effective dates, full text.
- **Record** – one entry in the organization's records (a registration attempt, an appointment): who
  (`person_id`), which unit, which item, status and reason code.
- **Request** – a question or complaint from a person: who sent it, subject, body, priority, status and the
  item it is about (if known).

### Part 2 – Knowledge Base and AI Foundation

- **SearchResult** – one document chunk returned by search: text, source file, document type, section,
  score (0–1) and metadata.

### Part 3 – Change Watch Agents

- **Requirement** – one concrete rule taken from a change document, with the exact quote and where it is.
- **ChangeSummary** – the Change Watcher's output: title, scope, effective date, short summary and the list
  of requirements.
- **Impact** – one requirement's effect on one unit: affected stakeholder groups, severity, reason, sources.
- **ImpactReport** – the Impact Analyst's output: all impacts plus requirements that matched no unit.
- **Check** – a way to verify an action item is done: steps and expected result.
- **ActionItem** – the Action Planner's output: a piece of work with unit, stakeholders, owner role, due date,
  checks, sources and review status.

### Part 4 – Request Desk Agent and Orchestrator

- **Investigation** – the Request Investigator's output: the item, reason code, root cause, records used as
  evidence, document sources, draft reply, confidence and whether to escalate.
- **TaskStep** – one step of a task with status, times, error and a progress message.
- **Task** – one run of a workflow for one template: type (change or request), status, steps and outputs.

### Part 5 – Website, Safety and Evaluation

- **ReviewDecision** – a person's approve / edit / reject decision on one output, with comment and time.
- **AuditEvent** – one line in the audit log: who did what, on which task, for which template, and when.

## Public functions

Every Part 1 and Part 2 function takes an optional `template_id` (none = the active template).

| Part | Function | What it does |
| --- | --- | --- |
| 1 | `tools.templates.list_templates()`, `load_template()` | List templates / load one `TemplateConfig` |
| 1 | `tools.changes.list_changes()`, `get_change()`, `parse_change(text)` | Read change documents; parse a pasted one |
| 1 | `tools.directory.list_units()`, `list_stakeholders()`, `stakeholders_for_unit(unit_id, scope)` | Units and stakeholder groups; who a unit's change affects (code, not AI) |
| 1 | `tools.requests.list_requests()`, `get_request()`, `set_request_status()` | Read requests; mark one answered |
| 1 | `tools.records.search_records(person_id, unit_id, item, status, since, until)` | Search records through the template's connector (read-only) |
| 1 | `tools.action_list.create_action_item()`, `list_action_items()` | Save an approved action item; list them |
| 2 | `knowledge_base.search.search(query, k, filters)` | Find the most relevant document chunks |
| 2 | `knowledge_base.ingest.ingest_all()` | Rebuild the search index (one collection per template) |
| 2 | `common.llm.complete_text()`, `complete_json(system, user, schema)` | The only way to call an LLM (masks personal data first) |
| 2 | `common.prompting.render(prompt_text, template)` | Fill `{organization}`, `{unit_label}`, `{prompt_hints}` … into a prompt |
| 3 | `watcher.summarize(doc)`, `impact.analyze(summary)`, `action_planner.plan(summary, report)` | The three Change Watch agents |
| 4 | `investigator.investigate(request)` | The Request Desk agent |
| 4 | `orchestrator.start_change_task()`, `start_request_task()`, `get_task()`, `list_tasks()`, `set_task_status()`, `update_output()`, `retry_task()`, `run_change_sync()`, `run_request_sync()` | Run and track tasks |
| 5 | `safety.masking.mask(text)` | Hide personal data |
| 5 | `safety.audit.log_event()`, `list_events()` | Write and read the audit log |

Module paths are relative to the part folder, for example `part1_templates.tools.records`,
`part2_knowledge.common.llm`, `part4_request_desk.orchestrator`, `part5_web.safety.masking`.
