"""Guide Section 11: both templates must satisfy the same invariants."""
from datetime import datetime
import hashlib
import importlib.util
import json
import re

from contracts.schemas import Record, Request, Stakeholder, Unit
from part1_templates.tests.conftest import TEMPLATES
from part1_templates.tools.changes import get_change, list_changes
from part1_templates.tools.directory import stakeholders_for_unit
from part1_templates.tools.templates import load_template

NOTE = "MOCK DATA – fictional, for a student prototype"


def _json(template_id, path, key):
    return json.loads((TEMPLATES / template_id / path).read_text(encoding="utf-8"))[key]


def _records(template_id):
    path = next((TEMPLATES / template_id / "records").glob("*.jsonl"))
    return [Record.model_validate(row) for row in map(json.loads, path.read_text(encoding="utf-8").splitlines()) if "_note" not in row]


def test_planted_requests_match_records(template_id):
    records = _records(template_id)
    requests = {row["request_id"]: Request.model_validate(row) for row in _json(template_id, "requests/requests.json", "requests")}
    for case in _json(template_id, "eval/request_eval.json", "cases"):
        request = requests[case["request_id"]]
        if case["expected_item"] is None:
            continue
        matches = [row for row in records if row.person_id == request.person_id and row.item == case["expected_item"]]
        if case["expected_escalate"]:
            assert not matches
        else:
            assert matches, case
            assert max(matches, key=lambda row: row.timestamp).reason_code == case["expected_reason_code"]
            assert all(row.timestamp <= request.created_at for row in matches)


def test_reason_codes_have_document_sections(template_id):
    template = load_template(template_id)
    document = (TEMPLATES / template_id / template.reason_codes_doc).read_text(encoding="utf-8")
    headings = set(re.findall(r"^## (\S+)\s*$", document, re.MULTILINE))
    assert {row.reason_code for row in _records(template_id) if row.reason_code} <= headings
    for row in _records(template_id):
        assert (row.reason_code is None) == (row.status in {"SETTLED", "REGISTERED"})


def test_units_and_memberships_are_consistent(template_id):
    units = [Unit.model_validate(row) for row in _json(template_id, "units.json", "units")]
    stakeholders = [Stakeholder.model_validate(row) for row in _json(template_id, "stakeholders.json", "stakeholders")]
    valid = {unit.unit_id for unit in units}
    assert len(valid) == len(units)
    assert all(set(group.units) <= valid for group in stakeholders)
    for case in _json(template_id, "eval/change_eval.json", "cases"):
        assert set(case["expected_units"]) <= valid
    banks = {group.stakeholder_id: group for group in stakeholders}
    for row in _records(template_id):
        assert row.unit_id in valid
        if row.person_id in banks:
            assert row.unit_id in banks[row.person_id].units
    assert all(row.template_id == template_id for row in _records(template_id))


def test_change_stakeholders_equal_scope_rule(template_id):
    for case in _json(template_id, "eval/change_eval.json", "cases"):
        document = get_change(case["change_id"], template_id)
        actual = {group.stakeholder_id for unit in case["expected_units"]
                  for group in stakeholders_for_unit(unit, scope=document.scope, template_id=template_id)}
        assert actual == set(case["expected_stakeholders"]), case
        assert document.published <= document.effective
        assert len(re.findall(r"^\d+\. ", document.text, re.MULTILINE)) == case["expected_requirements_min"]
        assert all(fact in document.text for fact in case["key_facts"])


def test_requesters_have_records_except_planned_escalations(template_id):
    people = {row.person_id for row in _records(template_id)}
    escalations = {case["request_id"] for case in _json(template_id, "eval/request_eval.json", "cases") if case["expected_escalate"]}
    for row in _json(template_id, "requests/requests.json", "requests"):
        assert row["person_id"] in people or row["request_id"] in escalations


def test_item_pattern_finds_every_named_item(template_id):
    template = load_template(template_id)
    requests = {row["request_id"]: row for row in _json(template_id, "requests/requests.json", "requests")}
    for case in _json(template_id, "eval/request_eval.json", "cases"):
        row = requests[case["request_id"]]
        assert row["item"] is None
        match = re.search(template.item_pattern, row["body"])
        item = (match.group(1) if match.lastindex else match.group()) if match else None
        assert item == case["expected_item"]


def test_markers_counts_history_and_sources(template_id):
    for path in (TEMPLATES / template_id).rglob("*"):
        if path.suffix in {".yaml", ".md", ".json", ".jsonl"}:
            content = path.read_text(encoding="utf-8")
            assert NOTE in content, path
            assert "ProgressSoft" not in content, path
            if path.suffix == ".json":
                assert json.loads(content)["_note"] == NOTE
            if path.suffix == ".jsonl":
                assert json.loads(content.splitlines()[0]) == {"_note": NOTE}
    records = _records(template_id)
    assert len(records) == (500 if template_id == "payments" else 250)
    assert len({row.record_id for row in records}) == len(records)
    if template_id == "payments":
        assert sum(row.reason_code is not None for row in records) == 75
        assert {row.timestamp.date().isoformat() for row in records} == {"2026-03-01", "2026-03-02", "2026-03-03"}
    else:
        assert len({row.person_id for row in records}) == 50
        assert all("2026-02-08" <= row.timestamp.date().isoformat() <= "2026-02-12" for row in records)
    for filename, expected in [("change_eval.json", 5 if template_id == "payments" else 3),
                               ("request_eval.json", 15 if template_id == "payments" else 10),
                               ("search_eval.json", 12 if template_id == "payments" else 8)]:
        assert len(_json(template_id, "eval/" + filename, "cases")) == expected
    assert len(_json(template_id, "history/past_requests.json", "requests")) == (8 if template_id == "payments" else 5)
    assert len(_json(template_id, "history/past_action_items.json", "action_items")) == (4 if template_id == "payments" else 2)
    for case in _json(template_id, "eval/search_eval.json", "cases"):
        assert (TEMPLATES.parents[1] / case["expected_source"]).exists()


def test_generators_reproduce_committed_bytes_twice(template_id, tmp_path):
    script = TEMPLATES / template_id / "generators/generate_records.py"
    spec = importlib.util.spec_from_file_location(f"generator_{template_id}", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    first, second = tmp_path / "first.jsonl", tmp_path / "second.jsonl"
    module.generate(first)
    module.generate(second)
    committed = next((TEMPLATES / template_id / "records").glob("*.jsonl"))
    hashes = [hashlib.sha256(path.read_bytes()).hexdigest() for path in [first, second, committed]]
    assert len(set(hashes)) == 1
    print(f"{template_id}: two runs and committed output SHA-256 {hashes[0]}")


def test_historical_action_examples_follow_contract_shape(template_id, action_model):
    for row in _json(template_id, "history/past_action_items.json", "action_items"):
        action = action_model.model_validate(row)
        change = get_change(action.change_id, template_id)
        allowed = {group.stakeholder_id for group in stakeholders_for_unit(action.unit_id, change.scope, template_id)}
        assert set(action.stakeholders) == allowed
        assert action.status == "approved"
        assert action.checks and action.sources
        for source in action.sources:
            document = (TEMPLATES.parents[1] / source["source"]).read_text(encoding="utf-8")
            assert source["text"] in document
