import pytest
from pydantic import BaseModel

from contracts.schemas import Investigation, Task, TaskStep


@pytest.mark.parametrize(
    "model",
    [Investigation, TaskStep, Task],
    ids=lambda model: model.__name__,
)
def test_part4_contract_examples_validate(model: type[BaseModel]) -> None:
    example = model.model_config["json_schema_extra"]["example"]

    model.model_validate(example)


@pytest.mark.parametrize(
    "model",
    [Investigation, TaskStep, Task],
    ids=lambda model: model.__name__,
)
def test_part4_contract_fields_have_descriptions(model: type[BaseModel]) -> None:
    assert all(field.description for field in model.model_fields.values())
