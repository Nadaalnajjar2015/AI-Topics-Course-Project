import re

import pytest

from contracts.schemas import ChangeDocument, Record, Request, Stakeholder, TemplateConfig, Unit
from part1_templates.tools.templates import list_templates, load_template


@pytest.mark.parametrize("model", [TemplateConfig, Unit, Stakeholder, ChangeDocument, Record, Request])
def test_part1_contract_examples_and_field_descriptions(model):
    example = model.model_config["json_schema_extra"]["example"]
    assert model.model_validate(example)
    assert all(field.description for field in model.model_fields.values())
    assert all(not word in name for name in model.model_fields for word in ["bank_", "payment_", "student_"])


def test_template_configuration_and_item_extraction(template_id):
    template = load_template(template_id)
    assert isinstance(template, TemplateConfig)
    body, expected = (("Why was payment 7731 rejected?", "7731") if template_id == "payments"
                      else ("Why can't I register for SE301?", "SE301"))
    match = re.search(template.item_pattern, body)
    assert (match.group(1) if match.lastindex else match.group()) == expected
    assert set(template.labels) == {"unit", "units", "stakeholder", "stakeholders", "person", "record", "item", "change", "request", "reviewer"}


def test_list_templates():
    assert [template.id for template in list_templates()] == ["payments", "university"]
    assert [template.id for template in list_templates("university")] == ["university"]
