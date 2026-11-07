import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from part1_templates.tools.templates import load_template
from part2_knowledge.common.config import _load_settings, settings


@pytest.fixture(autouse=True)
def isolated_environment():
    with patch.dict(os.environ, {}, clear=True):
        yield


def test_defaults_and_runtime_creation(tmp_path, monkeypatch):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    loaded = _load_settings(tmp_path)
    assert loaded.active_template == "payments"
    assert loaded.templates_dir == tmp_path / "part1_templates/templates"
    assert loaded.llm_provider == "fake"
    assert loaded.llm_model == "qwen2.5:7b"
    assert loaded.ollama_base_url == "http://localhost:11434"
    assert loaded.anthropic_api_key == loaded.openai_api_key == ""
    assert loaded.chroma_dir == tmp_path / "runtime/chroma"
    assert loaded.app_db == tmp_path / "runtime/app.db"
    assert loaded.llm_timeout_seconds == 120
    assert loaded.llm_max_retries == 1
    assert (tmp_path / "runtime").is_dir()
    assert not (elsewhere / "runtime").exists()


def test_dotenv_values_types_and_environment_precedence(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "ACTIVE_TEMPLATE=university\nTEMPLATES_DIR=fixtures\nLLM_PROVIDER=ollama\n"
        "LLM_MODEL=test-model\nOLLAMA_BASE_URL=http://localhost:1234\n"
        "ANTHROPIC_API_KEY=fictional-anthropic-key\nOPENAI_API_KEY=fictional-openai-key\n"
        "CHROMA_DIR=custom/chroma\nAPP_DB=custom/app.db\n"
        "LLM_TIMEOUT_SECONDS=30\nLLM_MAX_RETRIES=2\n", encoding="utf-8")
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    loaded = _load_settings(tmp_path)
    assert loaded.active_template == "university"
    assert loaded.llm_provider == "fake"
    assert loaded.llm_model == "test-model"
    assert loaded.ollama_base_url == "http://localhost:1234"
    assert loaded.templates_dir == tmp_path / "fixtures"
    assert loaded.chroma_dir == tmp_path / "custom/chroma"
    assert loaded.app_db == tmp_path / "custom/app.db"
    assert loaded.llm_timeout_seconds == 30 and loaded.llm_max_retries == 2
    assert loaded.anthropic_api_key == "fictional-anthropic-key"
    assert loaded.openai_api_key == "fictional-openai-key"
    assert "fictional-anthropic-key" not in repr(loaded)
    assert "fictional-openai-key" not in repr(loaded)


def test_absolute_paths_and_empty_values(tmp_path, monkeypatch):
    target = tmp_path / "absolute"
    monkeypatch.setenv("CHROMA_DIR", str(target))
    monkeypatch.setenv("LLM_PROVIDER", "")
    assert _load_settings(tmp_path).chroma_dir == target
    assert _load_settings(tmp_path).llm_provider == "fake"


@pytest.mark.parametrize("name,value", [
    ("LLM_TIMEOUT_SECONDS", "0"), ("LLM_TIMEOUT_SECONDS", "invalid"),
    ("LLM_MAX_RETRIES", "-1"), ("LLM_PROVIDER", "unknown"),
])
def test_invalid_settings_fail_clearly(tmp_path, monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(ValidationError, match=name.lower()):
        _load_settings(tmp_path)


def test_part1_uses_shared_active_template(monkeypatch):
    monkeypatch.setattr(settings, "active_template", "university")
    assert load_template().id == "university"
    assert load_template("payments").id == "payments"
