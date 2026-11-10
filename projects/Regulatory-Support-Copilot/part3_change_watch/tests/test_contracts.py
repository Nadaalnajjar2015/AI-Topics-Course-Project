from inspect import isclass
import json

from pydantic import BaseModel
import pytest

from contracts import schemas

MODELS = [value for value in vars(schemas).values() if isclass(value)
          and issubclass(value, BaseModel) and value.__module__ == schemas.__name__]


@pytest.mark.parametrize("model", MODELS, ids=lambda m: m.__name__)
def test_contract_examples_descriptions_and_json_round_trip(model):
    example = model.model_config["json_schema_extra"]["example"]
    result = model.model_validate(example)
    payload = result.model_dump(mode="json")
    assert model.model_validate(json.loads(json.dumps(payload))) == result
    assert all(field.description for field in model.model_fields.values())


def test_part3_agreed_fields():
    assert set(schemas.Requirement.model_fields) == {
        "requirement_id", "description", "category", "mandatory", "source_quote", "source_location"}
    assert set(schemas.ChangeSummary.model_fields) == {
        "change_id", "template_id", "title", "scope", "effective_date", "summary_text", "requirements"}
    assert set(schemas.ImpactReport.model_fields) == {"change_id", "impacts", "unmatched_requirements"}


@pytest.mark.parametrize("model,field,value", [(schemas.Impact,"severity","critical"),
    (schemas.ActionItem,"status","auto_approved"), (schemas.Requirement,"category","organization_specific")])
def test_literal_constraints(model, field, value):
    payload = dict(model.model_config["json_schema_extra"]["example"])
    payload[field] = value
    with pytest.raises(ValueError):
        model.model_validate(payload)
