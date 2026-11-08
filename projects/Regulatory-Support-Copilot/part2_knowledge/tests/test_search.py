from math import sqrt

import pytest

from contracts.schemas import SearchResult
from part2_knowledge.common.config import settings
from part2_knowledge.common.privacy import PRIVACY_METADATA_KEY, PRIVACY_VERSION
from part2_knowledge.knowledge_base import _store
from part2_knowledge.knowledge_base.search import search


def _collection(client, template_id, metadata_rows=None, embeddings=None):
    collection = client.create_collection(f"kb_{template_id}", embedding_function=_store._embedding_function(),
                                          metadata={PRIVACY_METADATA_KEY: PRIVACY_VERSION},
                                          configuration={"hnsw": {"space": "cosine"}})
    if metadata_rows:
        rows = [{"source": f"fixtures/{template_id}/guide.md", "doc_type": "document", "location": str(index),
                 "template_id": template_id, **metadata} for index, metadata in enumerate(metadata_rows)]
        collection.add(ids=[str(index) for index in range(len(rows))],
                       documents=[f"Passage {index}" for index in range(len(rows))], metadatas=rows,
                       embeddings=embeddings)
    return collection


def test_filters_use_and_and_missing_matches_return_empty(tiny_store):
    _collection(tiny_store, "payments", [{"unit_id": "ACH"}, {"unit_id": "IPS"},
                {"doc_type": "reason_codes", "reason_code": "AC04"}])
    assert len(search("axis")) == 3
    results = search("axis", filters={"doc_type": "document", "unit_id": "ACH"})
    assert len(results) == 1 and isinstance(results[0], SearchResult)
    assert results[0].metadata["unit_id"] == "ACH"
    assert search("axis", filters={"unit_id": "missing"}) == []
    assert search("axis", filters={"unknown_key": "missing"}) == []
    assert search("axis", filters={"reason_code": "AC04"})[0].doc_type == "reason_codes"


def test_templates_and_metadata_ownership_never_mix(tiny_store, monkeypatch):
    _collection(tiny_store, "payments", [{}, {"template_id": "university"}])
    _collection(tiny_store, "university", [{}])
    monkeypatch.setattr(settings, "active_template", "university")
    assert all(result.metadata["template_id"] == "university" for result in search("axis"))
    results = search("axis", template_id="payments")
    assert len(results) == 1 and results[0].metadata["template_id"] == "payments"
    assert search("axis", filters={"template_id": "university"}, template_id="payments") == []


def test_cosine_scores_limits_and_k(tiny_store):
    _collection(tiny_store, "payments", [{}, {}, {}],
                embeddings=[[1.0, 0.0, 0.0], [1 / 3, sqrt(8) / 3, 0.0], [-1.0, 0.0, 0.0]])
    results = search("axis", k=100)
    assert [result.score for result in results] == [1.0, 0.333, 0.0]
    assert len(search("axis", k=1)) == 1
    assert search("axis", k=0) == []


@pytest.mark.parametrize("existing", [False, True])
def test_missing_or_empty_collection_has_actionable_error(tiny_store, existing):
    if existing:
        _collection(tiny_store, "payments")
    with pytest.raises(RuntimeError, match="Knowledge base for 'payments' is empty") as error:
        search("axis")
    assert "python -m part2_knowledge.knowledge_base.ingest" in str(error.value)


@pytest.mark.parametrize("kwargs,message", [
    ({"k": -1}, "nonnegative integer"), ({"k": 1.5}, "nonnegative integer"),
    ({"k": True}, "nonnegative integer"), ({"filters": {"unit_id": None}}, "finite scalar"),
    ({"filters": {"$or": []}}, "not operators"), ({"filters": {"value": float("nan")}}, "finite scalar"),
])
def test_invalid_query_arguments_fail_clearly(tiny_store, kwargs, message):
    with pytest.raises(ValueError, match=message):
        search("axis", **kwargs)


def test_blank_query_and_unknown_template_are_clear(tiny_store):
    with pytest.raises(ValueError, match="must not be empty"):
        search(" \n")
    with pytest.raises(KeyError, match="not found"):
        search("axis", template_id="unknown")
