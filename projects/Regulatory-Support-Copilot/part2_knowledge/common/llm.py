"""Single LLM doorway; this first delivery supports offline fake responses."""
from copy import deepcopy
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from part2_knowledge.common.config import settings
from part2_knowledge.common.privacy import PrivacyError, mask_text, sanitize, sanitize_schema

Model = TypeVar("Model", bound=BaseModel)


class LLMError(RuntimeError):
    """An unsupported provider or unusable structured response."""


def _masked_prompts(system: str, user: str) -> tuple[str, str]:
    return mask_text(system), mask_text(user)


def _require_fake() -> None:
    if settings.llm_provider != "fake":
        raise LLMError(f"Provider '{settings.llm_provider}' is not implemented yet; use LLM_PROVIDER=fake.")


def _fake_text(system: str, user: str) -> str:
    return "Fake response for development; no language model was called."


def _fake_json(system: str, user: str, schema: dict):
    if "example" not in schema:
        raise LLMError(f"{schema['title']} needs a json_schema_extra['example'] for the fake provider.")
    return deepcopy(schema["example"])


def complete_text(system: str, user: str) -> str:
    """Protect prompts and response text at the provider boundary."""
    _require_fake()
    return mask_text(_fake_text(*_masked_prompts(system, user)))


def complete_json(system: str, user: str, schema: type[Model]) -> Model:
    """Protect prompts, schema examples and output, then validate the contract."""
    _require_fake()
    safe_schema = sanitize_schema(schema.model_json_schema())
    response = _fake_json(*_masked_prompts(system, user), safe_schema)
    try:
        result = schema.model_validate(sanitize(response))
        payload = result.model_dump(mode="json")
        safe_payload = sanitize(payload)
        if safe_payload != payload:
            result = schema.model_validate(safe_payload)
            if sanitize(result.model_dump(mode="json")) != result.model_dump(mode="json"):
                raise PrivacyError("Contract validation reintroduced private data; processing stopped.")
        return result
    except ValidationError:
        raise LLMError(f"The fake example for {schema.__name__} does not validate.") from None
