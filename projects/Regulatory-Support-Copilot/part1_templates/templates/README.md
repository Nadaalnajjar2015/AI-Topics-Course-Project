# Organization templates

All data is fictional. Each folder represents one organization and follows the same structure. The engine uses generic contracts; labels and prompt hints supply the organization's vocabulary.

| File or folder | Format and purpose |
| --- | --- |
| `template.yaml` | All eleven `TemplateConfig` keys; YAML comment marks mock data |
| `units.json` | `{"_note": "…", "units": [Unit, …]}` |
| `stakeholders.json` | `{"_note": "…", "stakeholders": [Stakeholder, …]}` |
| `documents/*.md` | Mock marker first, then title and `##` sections for ingestion |
| `changes/*.md` | YAML header, mock marker, numbered requirements and one background sentence |
| `records/*.jsonl` | First line `{"_note": "MOCK DATA – fictional, for a student prototype"}`, then one `Record` per line |
| `requests/requests.json` | `{"_note": "…", "requests": [Request, …]}` |
| `history/past_requests.json` | `{"_note": "…", "requests": [{question, root_cause, resolution, reason_code}, …]}` |
| `history/past_action_items.json` | `{"_note": "…", "action_items": [ActionItem, …]}` |
| `eval/*_eval.json` | `{"_note": "…", "cases": […]}`; individual cases follow Guide Section 10 |
| `generators/generate_records.py` | Seed-42 generator with planted evidence at the top |

The note text is always `MOCK DATA – fictional, for a student prototype`. JSON envelopes keep the marker valid JSON while retaining arrays of ordinary contract objects. Consumers should read the documented collection key and ignore `_note`. The `cases` envelope needs agreement from Part 5 before integration; draft issue text is in [TEAM_ISSUES.md](../TEAM_ISSUES.md).

## Configuration

`template.yaml` requires `id`, `organization`, `languages`, `labels`, `connector`, `item_pattern`, `reason_codes_doc`, `prompt_hints`, `action_item_fields` and `reviewers`. Its `id` must match its folder name. Labels cover `unit`, `units`, `stakeholder`, `stakeholders`, `person`, `record`, `item`, `change`, `request` and `reviewer`.

An item regex uses capture group 1 if present; otherwise its whole match is the item. Payments extracts `7731` from `payment 7731`; university extracts `SE301`. Requests intentionally leave `item` null so the investigator can extract it. A null record `reason_code` always means success.

Change scope is `all`, a stakeholder type, the name of an attribute whose value is boolean true, or an attribute comparison such as `country=Country X`. Unit membership is checked before scope. CHG-P-002's ACH/IPS union therefore contains BANK-A, BANK-B and BANK-E; CHG-U-001 includes STU-INTL as well as the two computing cohorts.

Change headers contain `change_id`, `template_id`, `title`, `issuer`, `scope`, `published` and `effective` (nullable). Keep the opening `---` on line one, as in the guide's parser example, and put the mock marker immediately after the closing `---`. `parse_change()` preserves the full source for citations and checks template ownership and date order.

## Add a hospital template

1. Copy an existing folder to `hospital/` and change its `template.yaml` ID to `hospital`.
2. Set a fictional organization name, labels such as Department, Patient group and Appointment record, an appointment item regex, prompt hints, reviewer roles and the reason-code document path.
3. Replace units, stakeholder groups, documents, changes, requests, history and evaluation cases. Set every embedded `template_id` to `hospital`; keep references, scope rules, reasons and dates consistent.
4. Select an existing connector if its JSONL filename and schema suit the records. Both existing connectors accept `template_id` and resolve their file inside that folder. Otherwise add an `AppointmentLookup(RecordConnector)` with the same six-filter `search()` signature and register it as `appointment_lookup` in `connectors/__init__.py`. A new source adapter may require code; existing tools and agents do not.
5. Include the new ID in the parametrized consistency tests, run `pytest part1_templates/tests`, then ask Part 2 to run `python -m part2_knowledge.knowledge_base.ingest` once its ingestion module exists. `list_templates()` discovers the new YAML automatically; Part 5's eventual switcher can use that list.

The existing transaction connector expects `records/transactions.jsonl`; the registration connector expects `records/registrations.jsonl`. Connectors never write, return at most 200 records newest first, and combine filters. Planted data must not be overwritten by random background records. Keep generator and committed output changes together.
