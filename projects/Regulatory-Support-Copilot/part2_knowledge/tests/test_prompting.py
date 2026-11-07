import pytest

from part1_templates.tools.templates import load_template
from part2_knowledge.common.prompting import load_prompt, render


@pytest.mark.parametrize("template_id,unit,stakeholder", [
    ("payments", "Product module", "Client bank"),
    ("university", "Study program", "Student group"),
])
def test_all_template_placeholders_and_extra_data(template_id, unit, stakeholder):
    template = load_template(template_id)
    prompt = ("{organization}|{unit_label}|{unit_label_plural}|{stakeholder_label}|"
              "{stakeholder_label_plural}|{person_label}|{record_label}|{item_label}|"
              "{change_label}|{request_label}|{reviewer}|{prompt_hints}|{units}|{document}")
    text = render(prompt, template, units="allowed units", document="<document>data</document>")
    assert unit in text and stakeholder in text
    assert text.split("|") == [template.organization, template.labels["unit"], template.labels["units"],
        template.labels["stakeholder"], template.labels["stakeholders"], template.labels["person"],
        template.labels["record"], template.labels["item"], template.labels["change"],
        template.labels["request"], template.labels["reviewer"], template.prompt_hints,
        "allowed units", "<document>data</document>"]


@pytest.mark.parametrize("placeholder", ["unit_labl", "units", "organization.missing"])
def test_unknown_placeholder_names_are_clear(placeholder):
    with pytest.raises(ValueError, match="Unknown prompt placeholder") as error:
        render("{" + placeholder + "}", load_template())
    assert placeholder in str(error.value)


def test_inserted_braces_are_data_and_literal_json_braces_work():
    text = render('{{"text": "{document}"}}', load_template(), document="{organization}")
    assert text == '{"text": "{organization}"}'


def test_load_prompt_reads_utf8(tmp_path):
    path = tmp_path / "prompt.md"
    path.write_text("مرحبا {organization}", encoding="utf-8")
    assert render(load_prompt(path), load_template()).startswith("مرحبا Cedar Payment Systems")


def test_load_prompt_reports_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_prompt(tmp_path / "missing.md")
