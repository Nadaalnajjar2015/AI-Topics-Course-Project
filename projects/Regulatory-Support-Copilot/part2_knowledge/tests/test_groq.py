"""Offline Groq SDK boundary tests; never contact Groq or touch the KB."""
import json
import sys
from types import SimpleNamespace

from pydantic import BaseModel, Field, field_validator
import pytest

from part2_knowledge.common import llm, privacy
from part2_knowledge.common.config import Settings, _load_settings, settings


class Answer(BaseModel):
    value: str
    model_config = {"json_schema_extra": {"example": {"value": "ops@example.test"}}}


@pytest.fixture
def sdk(monkeypatch):
    seen = {"content": '{"value":"accepted"}', "finish_reason": "stop"}

    class Client:
        def __init__(self, **kwargs):
            seen["configuration"] = kwargs
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

        def __enter__(self):
            return self

        def __exit__(self, *args):
            seen["closed"] = True

        def create(self, **kwargs):
            seen["request"] = kwargs
            if "error" in seen:
                raise seen["error"]
            if seen.get("no_choices"):
                return SimpleNamespace(choices=[])
            return SimpleNamespace(choices=[SimpleNamespace(
                finish_reason=seen["finish_reason"], message=SimpleNamespace(
                    content=seen["content"], refusal=seen.get("refusal")))])

    monkeypatch.setitem(sys.modules, "groq", SimpleNamespace(Groq=Client))
    monkeypatch.setattr(settings, "llm_provider", "groq")
    monkeypatch.setattr(settings, "groq_api_key", "fictional-test-key")
    monkeypatch.setattr(settings, "llm_model", "openai/gpt-oss-20b")
    return seen


def test_groq_environment_and_secret_repr(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "fictional-test-key")
    loaded = _load_settings(tmp_path)
    assert loaded.llm_provider == "groq" and loaded.groq_api_key == "fictional-test-key"
    assert "fictional-test-key" not in repr(loaded)
    assert Settings().llm_provider == "fake" and Settings().llm_model == "qwen2.5:7b"


def test_structured_route_arguments_and_redaction(sdk):
    sdk["content"] = '{"value":"return@example.test"}'
    result = llm.complete_json("system@example.test", "user@example.test", Answer)
    assert isinstance(result, Answer) and result.value == "[REDACTED]"
    request = sdk["request"]
    assert request["model"] == settings.llm_model and request["temperature"] == 0
    assert request["response_format"]["type"] == "json_schema"
    assert request["response_format"]["json_schema"]["strict"] is False
    assert "@example.test" not in json.dumps(request)
    assert sdk["configuration"] == {"api_key": "fictional-test-key", "timeout": 120, "max_retries": 1}
    assert sdk["closed"]


def test_json_object_mode_other_model(sdk, monkeypatch):
    monkeypatch.setattr(settings, "llm_model", "llama-3.3-70b-versatile")
    assert llm.complete_json("", "", Answer).value == "accepted"
    assert sdk["request"]["response_format"] == {"type": "json_object"}
    assert '"properties"' in sdk["request"]["messages"][0]["content"]


def test_text_route_masks_both_sides(sdk):
    sdk["content"] = "Reply to return@example.test"
    assert llm.complete_text("ops@example.test", "account 0013100030212") == "Reply to [REDACTED]"
    assert "response_format" not in sdk["request"]
    assert sdk["request"]["messages"] == [
        {"role": "system", "content": "[REDACTED]"},
        {"role": "user", "content": "account [REDACTED]"}]


@pytest.mark.parametrize("content", ["not json", "```json\n{}\n```", '{"wrong":1}', '[]', '{"value":null}'])
def test_invalid_json_or_contract_explicit_no_fake_fallback(sdk, content, monkeypatch):
    sdk["content"] = content
    monkeypatch.setattr(llm, "_fake_json", lambda *args: pytest.fail("must not fallback"))
    with pytest.raises(llm.LLMError, match="JSON"):
        llm.complete_json("", "", Answer)


@pytest.mark.parametrize("code,detail", [(400,"unsupported"), (401,"authentication"), (403,"permission"),
                                        (404,"unavailable"), (422,"schema"), (429,"rate limit"), (500,"provider")])
def test_provider_errors_hide_bodies_and_credentials(sdk, code, detail):
    error = RuntimeError("fictional-test-key ops@example.test raw sensitive body")
    error.status_code = code
    sdk["error"] = error
    with pytest.raises(llm.LLMError, match=detail) as caught:
        llm.complete_text("", "")
    assert "fictional-test-key" not in str(caught.value) and "@" not in str(caught.value)
    assert caught.value.__suppress_context__


def test_transport_error_and_settings(sdk, monkeypatch):
    sdk["error"] = TimeoutError("sensitive transport error")
    monkeypatch.setattr(settings, "llm_timeout_seconds", 5)
    monkeypatch.setattr(settings, "llm_max_retries", 0)
    with pytest.raises(llm.LLMError, match="timeout"):
        llm.complete_text("", "")
    assert sdk["configuration"]["max_retries"] == 0 and sdk["configuration"]["timeout"] == 5


@pytest.mark.parametrize("change", [{"no_choices":True}, {"content":None}, {"content":" "},
                                    {"refusal":"refused"}, {"finish_reason":"length"},
                                    {"finish_reason":"content_filter"}])
def test_empty_refused_incomplete(sdk, change):
    sdk.update(change)
    with pytest.raises(llm.LLMError):
        llm.complete_text("", "")


def test_absent_key_never_contacts_sdk(sdk, monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "")
    with pytest.raises(llm.LLMError, match="credentials missing"):
        llm.complete_json("", "", Answer)
    assert "request" not in sdk


def test_missing_sdk_explicit(sdk, monkeypatch):
    monkeypatch.setitem(sys.modules, "groq", None)
    with pytest.raises(llm.LLMError, match="SDK missing"):
        llm.complete_text("", "")


def test_schema_defaults_and_output_private_fields(sdk):
    class Private(BaseModel):
        email: str = Field(default="default@example.test")
    sdk["content"] = '{}'
    assert llm.complete_json("", "", Private).email == "[REDACTED]"
    assert "default@example.test" not in json.dumps(sdk["request"])


def test_validator_reintroducing_data_fails_closed(sdk):
    class Unsafe(BaseModel):
        value: str
        @field_validator("value")
        @classmethod
        def leak(cls, value):
            return "private@example.test"
    with pytest.raises(privacy.PrivacyError, match="reintroduced"):
        llm.complete_json("", "", Unsafe)


def test_broken_privacy_hook_stops_before_network(sdk, monkeypatch):
    def broken(name):
        raise RuntimeError("sensitive details")
    monkeypatch.setattr(privacy, "import_module", broken)
    with pytest.raises(privacy.PrivacyError):
        llm.complete_text("", "")
    assert "request" not in sdk


def test_broken_output_hook_stops(sdk, monkeypatch):
    def hook(text):
        if "accepted" in text:
            raise RuntimeError("broken")
        return text
    monkeypatch.setattr(privacy, "import_module", lambda name: SimpleNamespace(mask=hook))
    with pytest.raises(privacy.PrivacyError):
        llm.complete_json("", "", Answer)


def test_closed_fully_required_schema_uses_strict_mode(sdk):
    class Closed(BaseModel):
        value: str
        model_config = {"extra":"forbid"}
    assert llm.complete_json("","",Closed).value == "accepted"
    assert sdk["request"]["response_format"]["json_schema"]["strict"] is True


def test_closed_schema_with_default_remains_best_effort(sdk):
    class OptionalField(BaseModel):
        value: str = "default"
        model_config = {"extra":"forbid"}
    llm.complete_json("","",OptionalField)
    assert sdk["request"]["response_format"]["json_schema"]["strict"] is False


def test_nested_open_object_remains_best_effort(sdk):
    class Metadata(BaseModel):
        value: str
        metadata: dict[str,str]
        model_config = {"extra":"forbid"}
    sdk["content"] = '{"value":"accepted","metadata":{}}'
    llm.complete_json("","",Metadata)
    assert sdk["request"]["response_format"]["json_schema"]["strict"] is False


def test_model_without_strict_support_remains_best_effort(sdk,monkeypatch):
    class Closed(BaseModel):
        value: str
        model_config = {"extra":"forbid"}
    monkeypatch.setattr(settings,"llm_model","openai/gpt-oss-safeguard-20b")
    llm.complete_json("","",Closed)
    assert sdk["request"]["response_format"]["json_schema"]["strict"] is False
