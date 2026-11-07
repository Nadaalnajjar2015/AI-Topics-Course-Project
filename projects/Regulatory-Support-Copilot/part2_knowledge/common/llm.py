"""Single LLM doorway; this first delivery supports offline fake responses."""
from copy import deepcopy
from importlib import import_module
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from part2_knowledge.common.config import settings

Model = TypeVar("Model", bound=BaseModel)


class LLMError(RuntimeError):
    """An unsupported provider or unusable structured response."""


def _masked_prompts(system: str, user: str) -> tuple[str, str]:
    try:
        mask = import_module("part5_web.safety.masking").mask
    except ModuleNotFoundError as exc:
        if exc.name not in {"part5_web", "part5_web.safety", "part5_web.safety.masking"}:
            raise
        return system, user
    return mask(system), mask(user)


def _require_fake() -> None:
    if settings.llm_provider != "fake":
        raise LLMError(f"Provider '{settings.llm_provider}' is not implemented yet; use LLM_PROVIDER=fake.")


def _fake_text(system: str, user: str) -> str:
    return "Fake response for development; no language model was called."


def _fake_json(system: str, user: str, schema: type[Model]) -> Model:
    extra = schema.model_config.get("json_schema_extra")
    if not isinstance(extra, dict) or "example" not in extra:
        raise LLMError(f"{schema.__name__} needs a json_schema_extra['example'] for the fake provider.")
    try:
        return schema.model_validate(deepcopy(extra["example"]))
    except ValidationError as exc:
        raise LLMError(f"The fake example for {schema.__name__} does not validate.") from exc


def complete_text(system: str, user: str) -> str:
    """Return fixed offline text after applying the available masking hook."""
    _require_fake()
    return _fake_text(*_masked_prompts(system, user))


def complete_json(system: str, user: str, schema: type[Model]) -> Model:
    """Return a fresh, validated copy of a model's Contract Day example."""
    _require_fake()
    return _fake_json(*_masked_prompts(system, user), schema)
