"""Keep Part 2 tests independent of a developer's chosen provider/template."""
import pytest

from part2_knowledge.common.config import PROJECT_ROOT, settings


@pytest.fixture(autouse=True)
def offline_settings(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "fake")
    monkeypatch.setattr(settings, "active_template", "payments")
    monkeypatch.setattr(settings, "templates_dir", PROJECT_ROOT / "part1_templates/templates")
