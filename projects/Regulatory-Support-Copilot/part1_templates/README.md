# Part 1: Templates, Mock Data and Connectors

**Owner:** Zain Allateef - zaynallateef
**Guide:** [Part 1 guide](../docs/source/01-Part1-Templates-Data-and-Connectors.md)

Fictional organization data and deterministic tools for the Regulatory & Support Copilot. Payments has 500 transactions, 15 requests and 5 circulars; university has 250 registrations, 10 requests and 3 circulars. Both include documents, history and evaluation answers. No LLM or external record service is required here.

| Folder | Contents |
| --- | --- |
| `templates/payments/` | Cedar Payment Systems data and record generator |
| `templates/university/` | Northfield University data and record generator |
| `connectors/` | Read-only connector interface, two implementations and `CONNECTORS` registry |
| `tools/` | Public template, change, directory, request, record and action functions |
| `tests/` | Contract, tool, connector, consistency and reproducibility tests |

## Run and test

Run commands from `projects/Regulatory-Support-Copilot/`, using Python 3.11+ with `pydantic>=2`, `pyyaml` and `pytest` from the existing requirements. For an isolated Windows setup:

```powershell
python -m venv part1_templates/.venv
.\part1_templates\.venv\Scripts\python.exe -m pip install "pydantic>=2" pyyaml pytest
.\part1_templates\.venv\Scripts\python.exe -m pytest part1_templates/tests
```

Regenerate the committed files with seed 42, then run tests again:

```powershell
python part1_templates/templates/payments/generators/generate_records.py
python part1_templates/templates/university/generators/generate_records.py
```

## Public tools

All calls below run from the project folder. Data comes back as shared Pydantic contract objects. Pass `template_id="university"` to use the other organization. Omitted IDs use Part 2's `settings.active_template`; until that module exists, the default is `payments`. Discovery with `list_templates()` always lists all templates.

```python
from part1_templates.tools import templates, changes, directory, requests, records, action_list

templates.list_templates()
templates.load_template("university")
changes.list_changes(template_id="payments")
document = changes.get_change("CHG-P-002", template_id="payments")
changes.parse_change(document.text, template_id="payments")
directory.list_units(template_id="payments")
directory.get_unit("ACH", template_id="payments")
directory.list_stakeholders(template_id="payments")
directory.stakeholders_for_unit("IPS", "country=Country X", template_id="payments")
requests.list_requests(template_id="payments")
requests.get_request("P-REQ-007", template_id="payments")
records.search_records(person_id="BANK-C", item="7731", template_id="payments")
action_list.list_action_items(template_id="payments")
```

Scope matching supports `all`, group type, a true attribute, and `key=value`. Record filters (`person_id`, `unit_id`, `item`, `status`, `since`, `until`) combine with AND. Results are newest first, at most 200. Date-only bounds include the entire day; naive fixture times are treated as UTC. Unknown lookup IDs or templates raise clear errors; a record search with no match returns `[]`.

Only invoke these writes after human review:

```python
requests.set_request_status("P-REQ-007", "answered", template_id="payments")
# approved_item must be an approved contracts.schemas.ActionItem supplied by Part 3.
action_list.create_action_item(approved_item, template_id="payments")
```

Writes are isolated in ignored `runtime/<template_id>/state.json`; template fixtures never change. Actions must reference a known change, unit and stakeholders, and duplicate IDs are rejected. History examples are ingested as evidence; they are not automatically added to runtime actions.

## Integration notes

The shared `ActionItem` contract is still absent. `create_action_item()` and nonempty action-list loading report that dependency clearly; action tests use a test-only fake. Settings use Part 2's module once supplied. See [draft teammate issues](TEAM_ISSUES.md), [template format and third-template instructions](templates/README.md), and [review checklist](REVIEW.md). JSON collection envelopes are documented there for ingestion and evaluation consumers.
