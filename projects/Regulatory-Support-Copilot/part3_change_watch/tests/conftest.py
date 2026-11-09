"""Case-matched mocked LLM and retrieval; these fixtures do not measure accuracy."""
import json
import re

import pytest

from contracts.schemas import SearchResult
from part1_templates.tools.directory import list_units
from part2_knowledge.common import llm
from part2_knowledge.common.config import PROJECT_ROOT, settings
from part3_change_watch import impact, action_planner
from part3_change_watch._support import Extraction, UnitSelection, DraftAction


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "fake")
    monkeypatch.setattr(settings, "active_template", "payments")
    monkeypatch.setattr(settings, "templates_dir", PROJECT_ROOT / "part1_templates/templates")


def source(template_id="payments", unit_id="ACH", doc_type="document"):
    path = f"part1_templates/templates/{template_id}/documents/{unit_id}.md"
    if template_id == "university":
        path = f"part1_templates/templates/{template_id}/documents/study_plan_{unit_id}.md"
        if not (PROJECT_ROOT / path).exists():
            path = f"part1_templates/templates/{template_id}/documents/registration_rules.md"
    return SearchResult(text=(PROJECT_ROOT / path).read_text(encoding="utf-8"), source=path,
                        location="Test retrieved passage", doc_type=doc_type, score=.8,
                        metadata={"template_id": template_id, "unit_id": unit_id})


@pytest.fixture
def semantic_mocks(monkeypatch):
    seen = {"llm": [], "search": []}

    def retrieval(query, k=5, filters=None, template_id=None):
        seen["search"].append((query, k, filters, template_id))
        if filters == {"doc_type": "past_action_item"}:
            return []
        return [source(template_id, u.unit_id) for u in list_units(template_id=template_id)]

    def complete(system, user, schema):
        seen["llm"].append((system, user, schema))
        payload = json.loads(user.split("\n", 1)[1].rsplit("\n", 1)[0])
        if schema is Extraction:
            return Extraction(summary_text=" ".join(s["text"] for s in payload["sections"]),
                              effective_date=None, effective_quote=None, requirements=[{
                                  "description": s["text"], "category": "operational", "mandatory": True,
                                  "source_quote": s["text"], "source_location": s["number"],
                              } for s in payload["sections"]])
        if schema is UnitSelection:
            context = json.dumps(payload["change_context"])
            affected = [u["unit_id"] for u in payload["units"] if re.search(
                r"(?<![\w-])" + re.escape(u["unit_id"]) + r"(?![\w-])", context)]
            return UnitSelection(units=[{
                "unit_id": uid, "reason": "The source requires a change to this unit's current policy.",
                "evidence_indices": [n for n, s in enumerate(payload["passages"]) if s["metadata"].get("unit_id") == uid],
                "raise_severity": False, "escalation_reason": "",
            } for uid in affected])
        assert schema is DraftAction
        rules = payload["requirements"]
        uid = payload["unit"]["unit_id"]
        return DraftAction(title=f"Update {uid} policy and verification",
                           description="\n".join(f"{r['requirement_id']}: {r['description']}" for r in rules),
                           owner_role=f"{uid} owner", checks=[
                               {"steps": [f"Configure {uid} for the new rules.", "Exercise a compliant case."],
                                "expected": "The compliant case meets the cited requirements."},
                               {"steps": ["Exercise a case violating the new rule."],
                                "expected": "The stated rejection or warning is produced."}])

    monkeypatch.setattr(llm, "complete_json", complete)
    monkeypatch.setattr(impact, "search", retrieval)
    monkeypatch.setattr(action_planner, "search", retrieval)
    return seen
