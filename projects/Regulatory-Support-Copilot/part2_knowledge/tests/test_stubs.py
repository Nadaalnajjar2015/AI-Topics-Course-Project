import subprocess
import sys

import pytest

from contracts.schemas import SearchResult
from part2_knowledge.common.config import PROJECT_ROOT, settings
from part2_knowledge.knowledge_base.ingest import ingest_all
from part2_knowledge.knowledge_base.search import search


def test_search_returns_contract_example_and_matches_filters():
    results = search("What does AC04 mean?", k=5,
                     filters={"doc_type": "reason_codes", "reason_code": "AC04"})
    assert len(results) == 1 and isinstance(results[0], SearchResult)
    assert results[0].metadata["template_id"] == "payments"
    assert results[0].location == "AC04"
    assert search("AC04", filters={"doc_type": "document"}) == []
    assert search("AC04", filters={"reason_code": "unknown"}) == []
    assert search("AC04", filters={"unit_id": "not-indexed"}) == []
    assert search("AC04", filters={"missing_key": None}) == []
    assert search("AC04", k=0) == []
    with pytest.raises(ValueError, match="k must be nonnegative"):
        search("AC04", k=-1)


def test_search_never_relabels_payments_evidence_as_university(monkeypatch):
    assert search("SE301", template_id="university") == []
    monkeypatch.setattr(settings, "active_template", "university")
    assert search("SE301") == []
    assert search("AC04", template_id="payments")[0].metadata["template_id"] == "payments"


def test_search_returns_fresh_copies():
    search("AC04")[0].metadata["template_id"] = "changed"
    assert search("AC04")[0].metadata["template_id"] == "payments"


def test_ingest_all_and_selected_template_are_explicit_stubs(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "chroma_dir", tmp_path / "unused-index")
    monkeypatch.setattr(settings, "active_template", "university")
    summaries = ingest_all()
    assert set(summaries) == {"payments", "university"}
    assert set(ingest_all("university")) == {"university"}
    for identifier, summary in summaries.items():
        assert summary["status"] == "stub"
        assert summary["collection"] == f"kb_{identifier}"
        assert summary["files_read"] == 0 and summary["chunks_by_doc_type"] == {}
    assert not settings.chroma_dir.exists()


def test_unknown_templates_fail_clearly():
    with pytest.raises(KeyError, match="not found"):
        search("test", template_id="unknown")
    with pytest.raises(KeyError, match="not found"):
        ingest_all("unknown")


def test_ingest_cli_marks_index_as_unbuilt():
    result = subprocess.run([sys.executable, "-m", "part2_knowledge.knowledge_base.ingest",
                             "--template", "university"], cwd=PROJECT_ROOT,
                            capture_output=True, text=True, check=True)
    assert "university: stub; no index built (kb_university)" in result.stdout
    assert "payments:" not in result.stdout
