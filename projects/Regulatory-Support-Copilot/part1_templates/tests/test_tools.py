from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import shutil
from types import SimpleNamespace

from pydantic import ValidationError
import pytest

from contracts import schemas
from part1_templates.tools import action_list, changes, directory, records, requests, templates
from part1_templates.tests.conftest import TEMPLATES


def test_default_and_active_template_settings(monkeypatch):
    assert templates.load_template().id == "payments"
    monkeypatch.setattr(templates, "_settings", lambda: SimpleNamespace(active_template="university", templates_dir=TEMPLATES))
    assert templates.load_template().id == "university"
    assert directory.list_units()[0].unit_id == "CS-BSc"


@pytest.mark.parametrize("identifier", ["unknown", "../payments", "", "PAYMENTS"])
def test_unknown_template_is_clear(identifier):
    with pytest.raises(KeyError, match="available templates: payments, university"):
        templates.load_template(identifier)


def test_changes_and_parser(template_id):
    documents = changes.list_changes(template_id)
    assert len(documents) == (5 if template_id == "payments" else 3)
    for document in documents:
        assert isinstance(document, schemas.ChangeDocument)
        assert changes.get_change(document.change_id, template_id) == document
        assert changes.parse_change(document.text, template_id) == document
        assert document.effective >= document.published
    for invalid in ["", "Not a header", "---\nchange_id: broken", "---\n- not-a-mapping\n---"]:
        with pytest.raises(ValueError):
            changes.parse_change(invalid, template_id)
    other = "university" if template_id == "payments" else "payments"
    with pytest.raises(ValueError, match="belongs to template"):
        changes.parse_change(documents[0].text, other)
    with pytest.raises(ValueError, match="must not precede"):
        changes.parse_change(documents[0].text.replace(str(documents[0].effective), "2020-01-01"), template_id)


def test_directory_functions(template_id):
    units = directory.list_units(template_id)
    assert len(units) == (5 if template_id == "payments" else 6)
    assert all(isinstance(unit, schemas.Unit) for unit in units)
    for unit in units:
        assert directory.get_unit(unit.unit_id, template_id) == unit
    assert all(isinstance(group, schemas.Stakeholder) for group in directory.list_stakeholders(template_id))


@pytest.mark.parametrize("template,unit,scope,expected", [
    ("payments", "ACH", None, {"BANK-A", "BANK-B", "BANK-C", "BANK-D"}),
    ("payments", "ACH", "all", {"BANK-A", "BANK-B", "BANK-C", "BANK-D"}),
    ("payments", "ACH", "central", {"BANK-A", "BANK-D"}),
    ("payments", "ACH", "commercial", {"BANK-B", "BANK-C"}),
    ("payments", "WAL", "wallet", {"BANK-E"}),
    ("payments", "ACH", "country=Country X", {"BANK-A", "BANK-B"}),
    ("payments", "IPS", "country=Country X", {"BANK-A", "BANK-B", "BANK-E"}),
    ("payments", "ACH", "missing", set()),
    ("payments", "ACH", "missing=value", set()),
    ("university", "SE-BSc", "students", {"STU-SE-2026", "STU-INTL"}),
    ("university", "SE-BSc", "staff", {"STAFF-ADVISORS"}),
    ("university", "SE-BSc", "international", {"STU-INTL"}),
    ("university", "INTL-OFF", "international=true", {"STU-INTL"}),
    ("university", "SE-BSc", "cohort=2026", {"STU-SE-2026"}),
    ("university", "SE-BSc", "international=false", set()),
    ("university", "INTL-OFF", "cohort", set()),
])
def test_every_scope_form(template, unit, scope, expected):
    assert {group.stakeholder_id for group in directory.stakeholders_for_unit(unit, scope, template)} == expected


@pytest.mark.parametrize("function,prefix", [(changes.get_change, "Change"), (directory.get_unit, "Unit"), (requests.get_request, "Request")])
def test_unknown_ids(function, prefix, template_id):
    with pytest.raises(KeyError, match=f"{prefix} .* not found in template {template_id}"):
        function("missing", template_id)
    with pytest.raises(KeyError):
        function("../other", template_id)
    with pytest.raises(KeyError):
        directory.stakeholders_for_unit("missing", template_id=template_id)


def test_request_status_is_runtime_only(template_id, isolated_runtime):
    path = TEMPLATES / template_id / "requests" / "requests.json"
    before = path.read_bytes()
    rows = requests.list_requests(template_id)
    assert len(rows) == (15 if template_id == "payments" else 10)
    assert all(isinstance(row, schemas.Request) and row.status == "open" for row in rows)
    identifier = rows[0].request_id
    assert requests.get_request(identifier, template_id) == rows[0]
    assert requests.set_request_status(identifier, "answered", template_id).status == "answered"
    assert requests.get_request(identifier, template_id).status == "answered"
    assert path.read_bytes() == before
    state_path = isolated_runtime / template_id / "state.json"
    assert json.loads(state_path.read_text())["request_statuses"][identifier] == "answered"
    with pytest.raises(ValidationError):
        requests.set_request_status(identifier, "unknown", template_id)
    with pytest.raises(KeyError):
        requests.set_request_status("missing", "answered", template_id)


def test_search_dispatch_and_combined_filters(template_id):
    if template_id == "payments":
        filters = dict(person_id="BANK-C", unit_id="ACH", item="7731", status="REJECTED",
                       since="2026-03-02", until="2026-03-02")
        expected_id, reason = "T-100457", "AC04"
    else:
        filters = dict(person_id="S-2291", unit_id="SE-BSc", item="SE301", status="BLOCKED",
                       since="2026-02-10", until="2026-02-10")
        expected_id, reason = "R-48213", "PREREQ_MISSING"
    matches = records.search_records(**filters, template_id=template_id)
    assert len(matches) == 1
    assert matches[0].record_id == expected_id and matches[0].reason_code == reason
    for name, value in filters.items():
        selected = {"item": filters["item"], name: value}
        assert expected_id in {row.record_id for row in records.search_records(**selected, template_id=template_id)}
    assert records.search_records(**{**filters, "status": "not-a-status"}, template_id=template_id) == []
    assert records.search_records(person_id="missing", template_id=template_id) == []
    results = records.search_records(template_id=template_id)
    assert len(results) == 200
    assert all(isinstance(row, schemas.Record) and row.template_id == template_id for row in results)
    assert [row.timestamp for row in results] == sorted((row.timestamp for row in results), reverse=True)
    exact = matches[0].timestamp.replace(tzinfo=timezone.utc)
    assert records.search_records(**{**filters, "since": exact, "until": exact}, template_id=template_id) == matches
    with pytest.raises(ValueError, match="since must not be after until"):
        records.search_records(since="2027-01-01", until="2026-01-01", template_id=template_id)


def _action(template_id):
    unit = "ACH" if template_id == "payments" else "SE-BSc"
    return dict(action_id=f"AI-TEST-{template_id}", change_id="CHG-P-002" if template_id == "payments" else "CHG-U-001",
                title="Review configuration", description="Apply the approved change and verify its checks.", unit_id=unit,
                stakeholders=[group.stakeholder_id for group in directory.stakeholders_for_unit(unit, template_id=template_id)],
                owner_role="Unit owner", due_before=None, checks=[], sources=[], status="approved")


def test_action_storage_uses_shared_model(template_id, action_model, isolated_runtime):
    assert action_list.list_action_items(template_id) == []
    item = action_model.model_validate(_action(template_id))
    assert action_list.create_action_item(item, template_id) == item.action_id
    assert action_list.list_action_items(template_id) == [item]
    other = "university" if template_id == "payments" else "payments"
    assert action_list.list_action_items(other) == []
    # A status update must preserve already-approved actions in the same state file.
    requests.set_request_status(requests.list_requests(template_id)[0].request_id, "answered", template_id)
    assert action_list.list_action_items(template_id) == [item]
    with pytest.raises(ValueError, match="already exists"):
        action_list.create_action_item(item, template_id)
    assert (isolated_runtime / template_id / "state.json").exists()


@pytest.mark.parametrize("override,error", [({"status": "pending_review"}, ValueError), ({"status": "rejected"}, ValueError),
    ({"unit_id": "missing"}, KeyError), ({"change_id": "missing"}, KeyError), ({"stakeholders": ["foreign"]}, ValueError)])
def test_action_rejects_unapproved_or_foreign_data(template_id, action_model, override, error):
    with pytest.raises(error):
        action_list.create_action_item({**_action(template_id), **override}, template_id)


def test_action_dependency_error_is_explicit(monkeypatch):
    monkeypatch.delattr(schemas, "ActionItem", raising=False)
    with pytest.raises(RuntimeError, match="Part 3 must provide"):
        action_list.create_action_item(_action("payments"), "payments")


def test_runtime_updates_do_not_lose_concurrent_statuses(template_id):
    identifiers = [row.request_id for row in requests.list_requests(template_id)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda identifier: requests.set_request_status(identifier, "answered", template_id), identifiers))
    assert all(row.status == "answered" for row in requests.list_requests(template_id))


@pytest.mark.parametrize("function", [changes.list_changes, changes.parse_change, directory.list_units, directory.list_stakeholders,
    directory.stakeholders_for_unit, requests.list_requests, requests.set_request_status, records.search_records,
    action_list.create_action_item, action_list.list_action_items])
def test_tools_reject_unknown_templates(function):
    args = {changes.parse_change: [""], directory.stakeholders_for_unit: ["ACH"], requests.set_request_status: ["missing", "answered"],
            action_list.create_action_item: [{}]}.get(function, [])
    with pytest.raises(KeyError, match="available templates"):
        function(*args, template_id="unknown")


def test_source_files_are_unchanged_by_read_tools(template_id):
    def digest():
        return {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (TEMPLATES / template_id).rglob("*") if path.is_file() and "__pycache__" not in path.parts}
    before = digest()
    changes.list_changes(template_id)
    directory.list_units(template_id)
    directory.list_stakeholders(template_id)
    requests.list_requests(template_id)
    records.search_records(template_id=template_id)
    assert digest() == before


def test_third_template_uses_existing_tools_and_connector(tmp_path, monkeypatch):
    """Reusing a source format only needs data/configuration changes."""
    root = tmp_path / "templates"
    destination = root / "hospital"
    shutil.copytree(TEMPLATES / "university", destination, ignore=shutil.ignore_patterns("__pycache__"))
    for path in destination.rglob("*"):
        if path.suffix in {".yaml", ".json", ".jsonl", ".md"}:
            content = path.read_text(encoding="utf-8").replace("university", "hospital").replace("Northfield University", "Fictional Hospital")
            path.write_text(content, encoding="utf-8")
    monkeypatch.setattr(templates, "_settings", lambda: SimpleNamespace(active_template="hospital", templates_dir=root))
    assert templates.load_template().organization == "Fictional Hospital"
    assert [template.id for template in templates.list_templates()] == ["hospital"]
    assert len(directory.list_units()) == 6
    assert len(requests.list_requests()) == 10
    assert len(changes.list_changes()) == 3
    matches = records.search_records(person_id="S-2291", item="SE301")
    assert len(matches) == 1 and matches[0].template_id == "hospital"


def test_unknown_configured_connector_is_clear(monkeypatch):
    template = templates.load_template("payments").model_copy(update={"connector": "missing"})
    monkeypatch.setattr(records, "load_template", lambda _: template)
    with pytest.raises(ValueError, match="Unknown connector 'missing'"):
        records.search_records(template_id="payments")
