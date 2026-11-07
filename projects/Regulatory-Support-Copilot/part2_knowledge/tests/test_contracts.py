"""Contract Day checks using the actual Part 1 evidence and history."""
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from contracts.schemas import SearchResult

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_search_result_example_validates_and_matches_ac04_source():
    example = SearchResult.model_config["json_schema_extra"]["example"]
    result = SearchResult.model_validate(example)
    document = (PROJECT_ROOT / result.source).read_text(encoding="utf-8")
    section = document.split("## AC04\n", 1)[1].split("\n## ", 1)[0].strip()

    assert result.text == section
    assert result.doc_type == "reason_codes"
    assert result.location == "AC04"
    assert result.metadata == {"template_id": "payments", "reason_code": "AC04"}
    assert SearchResult.model_validate_json(result.model_dump_json()) == result


def test_search_result_schema_describes_every_required_field():
    schema = SearchResult.model_json_schema()
    assert set(schema["required"]) == set(SearchResult.model_fields)
    assert all(field["description"] for field in schema["properties"].values())
    assert schema["properties"]["score"]["minimum"] == 0
    assert schema["properties"]["score"]["maximum"] == 1


@pytest.mark.parametrize("score", [0, 0.84, 1])
def test_search_result_accepts_score_boundaries(score):
    example = SearchResult.model_config["json_schema_extra"]["example"]
    assert SearchResult.model_validate({**example, "score": score}).score == score


@pytest.mark.parametrize("score", [-0.01, 1.01, float("nan"), float("inf"), -float("inf")])
def test_search_result_rejects_scores_outside_contract(score):
    example = SearchResult.model_config["json_schema_extra"]["example"]
    with pytest.raises(ValidationError) as error:
        SearchResult.model_validate({**example, "score": score})
    assert error.value.errors()[0]["loc"] == ("score",)


def test_search_result_supports_university_evidence():
    source = "part1_templates/templates/university/documents/registration_rules.md"
    document = (PROJECT_ROOT / source).read_text(encoding="utf-8")
    section = document.split("## PREREQ_MISSING\n", 1)[1].split("\n## ", 1)[0].strip()
    result = SearchResult.model_validate({
        "text": section, "source": source, "doc_type": "reason_codes",
        "location": "PREREQ_MISSING", "score": 0.9,
        "metadata": {"template_id": "university", "reason_code": "PREREQ_MISSING"},
    })
    assert "SE301 requires SE201" in result.text
    assert result.metadata["template_id"] == "university"


@pytest.mark.parametrize("template_id", ["payments", "university"])
def test_search_result_accepts_existing_historical_citations(template_id):
    path = PROJECT_ROOT / "part1_templates/templates" / template_id / "history/past_action_items.json"
    actions = json.loads(path.read_text(encoding="utf-8"))["action_items"]
    citations = [source for action in actions for source in action["sources"]]
    assert citations
    for source in citations:
        result = SearchResult.model_validate(source)
        assert result.text in (PROJECT_ROOT / result.source).read_text(encoding="utf-8")
