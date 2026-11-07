"""Keep Part 2 tests independent of a developer's chosen provider/template."""
import pytest
from chromadb.api.types import EmbeddingFunction

from part2_knowledge.common.config import PROJECT_ROOT, settings
from part2_knowledge.knowledge_base import _store


@pytest.fixture(autouse=True)
def offline_settings(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "fake")
    monkeypatch.setattr(settings, "active_template", "payments")
    monkeypatch.setattr(settings, "templates_dir", PROJECT_ROOT / "part1_templates/templates")


class TinyEmbedding(EmbeddingFunction):
    """Deterministic nonzero vectors for storage tests, not semantic quality."""

    def __init__(self):
        pass

    def __call__(self, input):
        return [[1.0 + text.lower().count("closed"), float(text.lower().count("prereq")),
                 float(text.lower().count("wallet"))] for text in input]

    @staticmethod
    def name():
        return "part2_test_embedding"

    def get_config(self):
        return {}

    @staticmethod
    def build_from_config(config):
        return TinyEmbedding()


@pytest.fixture
def tiny_store(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "chroma_dir", tmp_path / "chroma")
    embedding = TinyEmbedding()
    monkeypatch.setattr(_store, "_embedding_function", lambda: embedding)
    return _store._client()
