"""Real MiniLM quality gate; no mocked ranking, oracle filters or silent skips."""
import json

import pytest

from part2_knowledge.common.config import PROJECT_ROOT, settings
from part2_knowledge.knowledge_base.evaluation import evaluate_search, format_search_report
from part2_knowledge.knowledge_base.ingest import ingest_all

TEMPLATES = PROJECT_ROOT / "part1_templates/templates"
TEMPLATE_IDS = sorted(path.parent.name for path in TEMPLATES.glob("*/template.yaml"))


@pytest.fixture(scope="module")
def quality_index(tmp_path_factory):
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(settings, "templates_dir", TEMPLATES)
        patch.setattr(settings, "chroma_dir", tmp_path_factory.mktemp("quality-index"))
        summaries = ingest_all()
        assert set(summaries) == set(TEMPLATE_IDS)
        yield summaries


@pytest.mark.parametrize("template_id", TEMPLATE_IDS)
def test_search_quality_each_template(template_id, quality_index, capsys):
    path = TEMPLATES / template_id / "eval/search_eval.json"
    cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
    report = evaluate_search(cases, template_id)
    text = format_search_report(report)
    with capsys.disabled():
        print("\n" + text + "\n")
    assert report["total"] == len(cases)
    assert report["hit_at_5"] >= 0.8, text
