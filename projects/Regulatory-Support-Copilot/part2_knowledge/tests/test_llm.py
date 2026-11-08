from copy import deepcopy
from inspect import isclass
from types import SimpleNamespace

from pydantic import BaseModel
import pytest

from contracts import schemas
from part2_knowledge.common import llm
from part2_knowledge.common import privacy
from part2_knowledge.common.config import settings

CONTRACTS = [value for value in vars(schemas).values()
             if isclass(value) and issubclass(value, BaseModel) and value.__module__ == schemas.__name__]


@pytest.mark.parametrize("schema", CONTRACTS, ids=lambda schema: schema.__name__)
def test_complete_json_validates_every_current_contract(schema):
    result = llm.complete_json("System", "User", schema)
    assert isinstance(result, schema)
    assert result == schema.model_validate(privacy.sanitize(schema.model_config["json_schema_extra"]["example"]))


def test_fake_results_do_not_mutate_shared_examples():
    original = deepcopy(schemas.SearchResult.model_config["json_schema_extra"]["example"])
    first = llm.complete_json("", "", schemas.SearchResult)
    first.metadata["template_id"] = "changed"
    second = llm.complete_json("", "", schemas.SearchResult)
    assert second.metadata["template_id"] == "payments"
    assert schemas.SearchResult.model_config["json_schema_extra"]["example"] == original


def test_complete_text_is_fixed_offline_output():
    assert llm.complete_text("System", "User") == llm.complete_text("Other", "Text")
    assert "no language model was called" in llm.complete_text("", "")


@pytest.mark.parametrize("structured", [False, True])
def test_both_prompts_are_masked_before_fake_provider(monkeypatch, structured):
    seen = []
    monkeypatch.setattr(privacy, "import_module", lambda name: SimpleNamespace(
        mask=lambda text: f"MASKED:{text}" if text in {"System", "User"} else text))

    def provider(system, user, *schema):
        seen.append((system, user))
        return deepcopy(schema[0]["example"]) if schema else "fixed"

    monkeypatch.setattr(llm, "_fake_json" if structured else "_fake_text", provider)
    if structured:
        llm.complete_json("System", "User", schemas.SearchResult)
    else:
        llm.complete_text("System", "User")
    assert seen == [("MASKED:System", "MASKED:User")]


def test_missing_masking_module_uses_strict_local_redaction(monkeypatch):
    def missing(name):
        raise ModuleNotFoundError(name, name=name)

    monkeypatch.setattr(privacy, "import_module", missing)
    monkeypatch.setattr(llm, "_fake_text", lambda system, user: f"{system}|{user}")
    assert llm.complete_text("system", "user") == "system|user"
    assert "0013100030212" not in llm.complete_text("account 0013100030212", "user")


def test_existing_masking_dependency_failure_is_not_hidden(monkeypatch):
    def broken(name):
        raise ModuleNotFoundError("mask dependency missing", name="missing_mask_dependency")

    monkeypatch.setattr(privacy, "import_module", broken)
    with pytest.raises(privacy.PrivacyError, match="missing dependency"):
        llm.complete_text("", "")


@pytest.mark.parametrize("provider", ["ollama", "anthropic", "openai"])
def test_unimplemented_providers_are_explicit(monkeypatch, provider):
    monkeypatch.setattr(settings, "llm_provider", provider)
    with pytest.raises(llm.LLMError, match="use LLM_PROVIDER=fake"):
        llm.complete_text("", "")
    with pytest.raises(llm.LLMError, match="use LLM_PROVIDER=fake"):
        llm.complete_json("", "", schemas.SearchResult)


def test_missing_or_invalid_examples_raise_llm_error():
    class WithoutExample(BaseModel):
        value: int

    class InvalidExample(BaseModel):
        value: int
        model_config = {"json_schema_extra": {"example": {"value": "invalid"}}}

    with pytest.raises(llm.LLMError, match="WithoutExample needs"):
        llm.complete_json("", "", WithoutExample)
    with pytest.raises(llm.LLMError, match="InvalidExample does not validate"):
        llm.complete_json("", "", InvalidExample)
