import pytest

from contracts.schemas import SearchResult
from part2_knowledge.knowledge_base import evaluation


def _result(source, template="payments"):
    return SearchResult(text="Evidence", source=source, doc_type="document", location="Section",
                        score=0.5, metadata={"template_id": template})


def test_sixth_place_and_same_filename_in_other_directory_do_not_count(monkeypatch):
    expected = "documents/correct/guide.md"
    results = [_result("documents/wrong/guide.md")] * 5 + [_result(expected)]
    seen = []

    def lookup(query, **kwargs):
        seen.append(kwargs)
        return results

    monkeypatch.setattr(evaluation, "search", lookup)
    report = evaluation.evaluate_search([{"query": "Question", "expected_source": expected}], "payments")
    assert report["hits"] == 0 and report["hit_at_5"] == 0 and not report["passed"]
    assert seen == [{"k": 5, "template_id": "payments"}]
    assert "MISS" in evaluation.format_search_report(report)
    assert expected in evaluation.format_search_report(report)


def test_fifth_place_and_normalized_full_source_path_count(monkeypatch):
    expected = "documents/right/guide.md"
    monkeypatch.setattr(evaluation, "search", lambda *args, **kwargs: [
        _result("documents/wrong.md")] * 4 + [_result(expected)])
    report = evaluation.evaluate_search([{"query": "Question", "expected_source": expected.replace("/", "\\")}], "payments")
    assert report["hits"] == report["total"] == 1 and report["passed"]
    assert report["cases"][0]["rank"] == 5
    assert "100.0%" in evaluation.format_search_report(report)


def test_exact_threshold_and_no_results(monkeypatch):
    monkeypatch.setattr(evaluation, "search", lambda query, **kwargs: [] if query == "miss" else [_result("right.md")])
    cases = [{"query": "hit", "expected_source": "right.md"}] * 4 + [{"query": "miss", "expected_source": "right.md"}]
    report = evaluation.evaluate_search(cases, "payments")
    assert report["hit_at_5"] == 0.8 and report["passed"]
    assert "no results" in evaluation.format_search_report(report)
    report = evaluation.evaluate_search(cases + [{"query": "miss", "expected_source": "right.md"}], "payments")
    assert not report["passed"]


@pytest.mark.parametrize("cases", [[], {}, [{}], [{"query": "", "expected_source": "a.md"}],
                                   [{"query": "Question", "expected_source": "../a.md"}]])
def test_missing_empty_and_invalid_evaluation_data_fails(cases):
    with pytest.raises(ValueError):
        evaluation.evaluate_search(cases, "payments")


def test_other_template_evidence_is_an_error(monkeypatch):
    monkeypatch.setattr(evaluation, "search", lambda *args, **kwargs: [_result("a.md", "university")])
    with pytest.raises(RuntimeError, match="different template"):
        evaluation.evaluate_search([{"query": "Question", "expected_source": "a.md"}], "payments")
