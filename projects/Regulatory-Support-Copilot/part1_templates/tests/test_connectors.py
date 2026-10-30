from datetime import date, datetime, timezone
import hashlib
import json

import pytest

from contracts.schemas import Record
from part1_templates.connectors import CONNECTORS
from part1_templates.connectors.base import JsonlRecordConnector, RecordConnector
from part1_templates.tools.templates import load_template


def test_concrete_connectors_are_read_only(template_id):
    template = load_template(template_id)
    connector = CONNECTORS[template.connector]()
    before = hashlib.sha256(connector.path.read_bytes()).hexdigest()
    assert isinstance(connector, RecordConnector)
    records = connector.search()
    assert len(records) == 200
    assert all(isinstance(record, Record) and record.template_id == template_id for record in records)
    assert records == sorted(records, key=lambda row: (row.timestamp, row.record_id), reverse=True)
    assert hashlib.sha256(connector.path.read_bytes()).hexdigest() == before


def test_all_filters_and_time_boundaries(tmp_path):
    path = tmp_path / "records.jsonl"
    base = Record.model_config["json_schema_extra"]["example"]
    rows = [dict(base, record_id="old", timestamp="2026-03-01T23:59:59"),
            dict(base, record_id="target", timestamp="2026-03-02T09:12:03"),
            dict(base, record_id="wrong-person", person_id="BANK-A", timestamp="2026-03-02T09:12:04"),
            dict(base, record_id="end-of-day", timestamp="2026-03-02T23:59:59.999999"),
            dict(base, record_id="next-day", timestamp="2026-03-03T00:00:00")]
    path.write_text("\n".join(json.dumps(row) for row in [{"_note": "MOCK DATA"}, *rows]), encoding="utf-8")
    connector = JsonlRecordConnector(path, "payments")
    assert [row.record_id for row in connector.search(since=date(2026, 3, 2), until="2026-03-02")] == ["end-of-day", "wrong-person", "target"]
    exact = datetime(2026, 3, 2, 9, 12, 3, tzinfo=timezone.utc)
    assert [row.record_id for row in connector.search(since=exact, until="2026-03-02T11:12:03+02:00")] == ["target"]
    filters = dict(person_id="BANK-C", unit_id="ACH", item="7731", status="REJECTED", since="2026-03-02", until="2026-03-02")
    assert [row.record_id for row in connector.search(**filters)] == ["end-of-day", "target"]
    for name in ["person_id", "unit_id", "item", "status"]:
        assert connector.search(**{**filters, name: "not-a-match"}) == []
    with pytest.raises(ValueError):
        connector.search(since="not-a-date")
    with pytest.raises(TypeError):
        connector.search(since=42)
    with pytest.raises(ValueError, match="since must not be after until"):
        connector.search(since="2026-03-03", until="2026-03-01")
    foreign = dict(base, template_id="university")
    path.write_text(json.dumps(foreign), encoding="utf-8")
    with pytest.raises(ValueError, match="different template"):
        connector.search()


def test_connector_interface_requires_search():
    with pytest.raises(TypeError):
        RecordConnector()
