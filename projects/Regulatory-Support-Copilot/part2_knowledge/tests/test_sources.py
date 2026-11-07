from pathlib import Path
import shutil

import pytest
import yaml

from part2_knowledge.common.config import settings
from part2_knowledge.knowledge_base._sources import _load_chunks
from part2_knowledge.knowledge_base.ingest import ingest_all
from part2_knowledge.knowledge_base.search import search


@pytest.mark.parametrize("template_id", ["payments", "university"])
def test_loads_every_approved_source_type_with_stable_ids(template_id):
    chunks, files = _load_chunks(template_id)
    assert files == 15
    assert {chunk.metadata["doc_type"] for chunk in chunks} == {
        "document", "reason_codes", "unit", "stakeholder", "past_request", "past_action_item", "change"}
    assert len({chunk.id for chunk in chunks}) == len(chunks)
    assert chunks == _load_chunks(template_id)[0]
    for chunk in chunks:
        assert chunk.metadata["template_id"] == template_id
        assert all(key in chunk.metadata for key in ("source", "doc_type", "location"))
        assert all(part not in chunk.metadata["source"].split("/") for part in ("records", "requests", "eval"))
        assert "_note:" not in chunk.text
        assert all(isinstance(value, (str, int, float, bool)) for value in chunk.metadata.values())
        if chunk.metadata["doc_type"] == "reason_codes":
            assert chunk.metadata["reason_code"] == chunk.metadata["location"]
        if chunk.metadata["doc_type"] in {"unit", "past_action_item"}:
            assert "unit_id" in chunk.metadata
        if chunk.metadata["doc_type"] == "stakeholder":
            assert "stakeholder_id" in chunk.metadata
        if chunk.metadata["doc_type"] == "change":
            assert "change_id" in chunk.metadata and "effective" in chunk.metadata


@pytest.mark.parametrize("template_id,filename,unit_id", [
    ("payments", "ACH.md", "ACH"), ("university", "study_plan_SE-BSc.md", "SE-BSc"),
])
def test_unit_metadata_is_derived_from_template_unit_ids(template_id, filename, unit_id):
    chunks, _ = _load_chunks(template_id)
    matching = [chunk for chunk in chunks if chunk.metadata["source"].endswith("/" + filename)]
    assert matching and all(chunk.metadata["unit_id"] == unit_id for chunk in matching)


def test_reason_code_and_general_university_policy_are_both_available():
    chunks, _ = _load_chunks("university")
    sections = {chunk.metadata["location"]: chunk for chunk in chunks
                if chunk.metadata["source"].endswith("/registration_rules.md")}
    assert sections["PREREQ_MISSING"].metadata["doc_type"] == "reason_codes"
    assert sections["Credit limits"].metadata["doc_type"] == "document"
    assert "18 credits" in sections["Credit limits"].text


@pytest.fixture
def third_template(tmp_path, monkeypatch):
    root = tmp_path / "templates"
    destination = root / "clinic"
    shutil.copytree(settings.templates_dir / "university", destination,
                    ignore=shutil.ignore_patterns("__pycache__"))
    config_path = destination / "template.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["id"] = "clinic"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    for path in (destination / "changes").glob("*.md"):
        path.write_text(path.read_text(encoding="utf-8").replace("template_id: university", "template_id: clinic"),
                        encoding="utf-8")
    monkeypatch.setattr(settings, "templates_dir", root)
    return destination


def test_an_additional_template_loads_without_code_changes(third_template):
    chunks, files = _load_chunks("clinic")
    assert files == 15 and chunks
    assert all(chunk.metadata["template_id"] == "clinic" for chunk in chunks)
    assert all("/clinic/" in chunk.metadata["source"] for chunk in chunks)


def test_an_additional_template_ingests_and_searches_without_code_changes(third_template, tiny_store):
    summaries = ingest_all()
    assert set(summaries) == {"clinic"}
    assert summaries["clinic"]["collection"] == "kb_clinic"
    results = search("prereq", filters={"doc_type": "reason_codes", "reason_code": "PREREQ_MISSING"},
                     template_id="clinic")
    assert results and all(result.metadata["template_id"] == "clinic" for result in results)


def test_reason_document_cannot_escape_template(third_template):
    path = third_template / "template.yaml"
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    config["reason_codes_doc"] = "../../outside.md"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    with pytest.raises(ValueError, match="must stay inside"):
        _load_chunks("clinic")
