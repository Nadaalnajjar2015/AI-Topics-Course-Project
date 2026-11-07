import sys

import pytest

from part2_knowledge.common.config import settings
from part2_knowledge.knowledge_base import _store, ingest
from part2_knowledge.knowledge_base.chunking import Chunk
from part2_knowledge.knowledge_base.search import search


def test_ingest_all_sources_rebuilds_stable_isolated_cosine_collections(tiny_store, monkeypatch):
    monkeypatch.setattr(settings, "active_template", "university")
    summaries = ingest.ingest_all()
    assert set(summaries) == {"payments", "university"}
    before = {}
    for template_id, summary in summaries.items():
        collection = tiny_store.get_collection(summary["collection"], embedding_function=_store._embedding_function())
        assert summary["status"] == "ready" and summary["files_read"] == 15
        assert summary["chunks"] == collection.count() == sum(summary["chunks_by_doc_type"].values())
        assert collection.configuration["hnsw"]["space"] == "cosine"
        before[template_id] = sorted(collection.get()["ids"])
        results = search("axis", template_id=template_id)
        assert results and all(result.metadata["template_id"] == template_id for result in results)
    assert set(ingest.ingest_all("payments")) == {"payments"}
    for template_id, ids in before.items():
        assert sorted(tiny_store.get_collection(f"kb_{template_id}").get()["ids"]) == ids
    assert search("closed", filters={"doc_type": "reason_codes", "reason_code": "AC04"},
                  template_id="payments")[0].location == "AC04"
    assert search("prereq", filters={"doc_type": "reason_codes", "reason_code": "PREREQ_MISSING"},
                  template_id="university")[0].location == "PREREQ_MISSING"
    assert search("credits", filters={"doc_type": "document"}, k=1000, template_id="university")


def test_rebuild_removes_stale_chunks(tiny_store, monkeypatch):
    metadata = {"template_id": "payments", "source": "fixture.md", "doc_type": "document", "location": "Section"}
    chunks = [Chunk("fixture.md#0", "First", metadata), Chunk("fixture.md#1", "Second", metadata)]
    monkeypatch.setattr(ingest, "_load_chunks", lambda template_id: (chunks, 1))
    assert ingest.ingest_all("payments")["payments"]["chunks"] == 2
    chunks.pop()
    assert ingest.ingest_all("payments")["payments"]["chunks"] == 1
    assert tiny_store.get_collection("kb_payments").get()["ids"] == ["fixture.md#0"]


@pytest.mark.parametrize("failure", ["source", "embedding"])
def test_source_or_embedding_failure_preserves_previous_index(tiny_store, monkeypatch, failure):
    ingest.ingest_all("payments")
    before = sorted(tiny_store.get_collection("kb_payments").get()["ids"])

    def broken(*args, **kwargs):
        raise ValueError("fixture failure")

    if failure == "source":
        monkeypatch.setattr(ingest, "_load_chunks", broken)
    else:
        monkeypatch.setattr(_store, "_embedding_function", lambda: broken)
    with pytest.raises(ValueError, match="fixture failure"):
        ingest.ingest_all("payments")
    assert sorted(tiny_store.get_collection("kb_payments").get()["ids"]) == before


def test_ingest_cli_reports_actual_counts(tiny_store, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["ingest", "--template", "university"])
    ingest._main()
    output = capsys.readouterr().out
    assert "university: 15 files," in output and "kb_university" in output
    assert "reason_codes=" in output and "stub" not in output
    assert "payments:" not in output


def test_unknown_template_is_rejected_before_rebuilding(tiny_store):
    with pytest.raises(KeyError, match="not found"):
        ingest.ingest_all("unknown")
