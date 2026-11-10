from datetime import date, timedelta
import json

import pytest

from contracts.schemas import ChangeSummary, ImpactReport
from part1_templates.tools import action_list
from part1_templates.tools.changes import get_change
from part1_templates.tools.directory import stakeholders_for_unit
from part1_templates.tools.templates import load_template
from part2_knowledge.common import llm
from part3_change_watch import watcher, impact, action_planner, cli, quality_check
from part3_change_watch._support import UnitSelection, DraftAction, prompt
from part3_change_watch.tests.conftest import source


@pytest.fixture
def summary(semantic_mocks):
    return watcher.summarize(get_change("CHG-P-002", template_id="payments"))


@pytest.mark.parametrize("template_id,change_id,units,groups", [
    ("payments","CHG-P-002", {"ACH","IPS"}, {"BANK-A","BANK-B","BANK-E"}),
    ("university","CHG-U-001", {"CS-BSc","SE-BSc"}, {"STU-CS-2026","STU-SE-2026","STU-INTL"})])
def test_same_pipeline_and_deterministic_directory(semantic_mocks, monkeypatch, template_id, change_id, units, groups):
    monkeypatch.setattr(action_list, "create_action_item", lambda *a,**k: pytest.fail("no storage write"))
    before = action_list.list_action_items(template_id=template_id)
    outputs = cli.run(get_change(change_id, template_id=template_id))
    summary = ChangeSummary.model_validate(outputs["summary"])
    report = ImpactReport.model_validate(outputs["impact_report"])
    actions = outputs["action_items"]
    assert len(summary.requirements) == 3
    assert {i.unit_id for i in report.impacts} == units
    assert {s for i in report.impacts for s in i.stakeholders} == groups
    assert {a["unit_id"] for a in actions} == units and len(actions) == len(units)
    for action in actions:
        assert action["status"] == "pending_review" and 2 <= len(action["checks"]) <= 4
        assert action["due_before"] == summary.effective_date.isoformat()
        assert action["action_id"] == f"AI-{change_id}-{action['unit_id']}"
        assert all(r.requirement_id in action["description"] for r in summary.requirements)
        expected = sorted(g.stakeholder_id for g in stakeholders_for_unit(action["unit_id"], scope=summary.scope,
                                                                          template_id=template_id))
        assert action["stakeholders"] == expected
    assert action_list.list_action_items(template_id=template_id) == before
    template = load_template(template_id)
    assert all(template.organization in s and template.labels["unit"] in s
               for s, _, _ in semantic_mocks["llm"])
    assert all(call[3] == template_id for call in semantic_mocks["search"])
    assert any(k == 5 and f == {"doc_type":"document"} for _,k,f,_ in semantic_mocks["search"])
    assert any(k == 2 and f == {"doc_type":"past_action_item"} for _,k,f,_ in semantic_mocks["search"])


def selection(monkeypatch, ids, indices=None, escalation=False, reason=""):
    result = UnitSelection(units=[{"unit_id": uid, "reason":"Affected validation policy.",
                                  "evidence_indices": [0] if indices is None else indices,
                                  "raise_severity":escalation, "escalation_reason":reason} for uid in ids])
    monkeypatch.setattr(llm, "complete_json", lambda *args: result)


def test_invented_foreign_unit_and_duplicates_rejected(summary, monkeypatch):
    selection(monkeypatch, ["ACH", "ACH", "CS-BSc", "FABRICATED"])
    monkeypatch.setattr(impact, "search", lambda *a, **k: [source()])
    report = impact.analyze(summary)
    assert len(report.impacts) == 3 and all(i.unit_id == "ACH" for i in report.impacts)


def test_unmatched_and_empty_summary(summary, monkeypatch):
    selection(monkeypatch, ["FOREIGN"])
    assert impact.analyze(summary).unmatched_requirements == sorted(r.requirement_id for r in summary.requirements)
    assert impact.analyze(summary.model_copy(update={"requirements":[]})).impacts == []


@pytest.mark.parametrize("mandatory,days,expected", [(False,10,"low"), (True,0,"high"), (True,-1,"high"),
    (True,90,"high"), (True,91,"medium"), (True,None,"medium"), (False,None,"low")])
def test_severity_rules(mandatory, days, expected):
    today = date(2026,11,9)
    assert impact.initial_severity(mandatory, today + timedelta(days=days) if days is not None else None, today)[0] == expected


@pytest.mark.parametrize("indices,sources,expected", [([0],True,"high"), ([999],True,"low"), ([0],False,"low"), ([-1],True,"low")])
def test_missing_evidence_and_intact_citation(summary, monkeypatch, indices, sources, expected):
    cited = source()
    selection(monkeypatch, ["ACH"], indices)
    monkeypatch.setattr(impact,"search",lambda *a,**k: [cited] if sources else [])
    report = impact.analyze(summary)
    assert all(i.severity == expected for i in report.impacts)
    if expected == "high":
        assert all(i.sources == [cited] and i.sources[0].metadata == cited.metadata for i in report.impacts)
    else:
        assert all("No supporting documentation" in i.reason for i in report.impacts)


@pytest.mark.parametrize("reason,expected", [("", "low"), ("A documented operational consequence.","medium")])
def test_escalation_one_level_only_with_reason(summary, monkeypatch, reason, expected):
    summary = summary.model_copy(update={"requirements":[r.model_copy(update={"mandatory":False}) for r in summary.requirements]})
    selection(monkeypatch,["ACH"],escalation=True,reason=reason)
    monkeypatch.setattr(impact,"search",lambda *a,**k:[source()])
    assert all(i.severity == expected for i in impact.analyze(summary).impacts)


def test_other_unit_passage_not_counted_as_support(summary, monkeypatch):
    selection(monkeypatch,["ACH"])
    monkeypatch.setattr(impact,"search",lambda *a,**k:[source(unit_id="IPS")])
    assert all(i.severity == "low" and not i.sources for i in impact.analyze(summary).impacts)


@pytest.mark.parametrize("metadata,path,doc_type", [
    ({"template_id":"university"},None,"document"), ({},None,"document"),
    ({"template_id":"payments"},"part1_templates/templates/university/documents/file.md","document"),
    ({"template_id":"payments"},"part1_templates/templates/payments/../university/file.md","document"),
    ({"template_id":"payments"},None,"past_request")])
def test_cross_template_citations_fail_closed(summary, monkeypatch, metadata, path, doc_type):
    cited = source().model_copy(update={"metadata":metadata, "doc_type":doc_type})
    if path:
        cited = cited.model_copy(update={"source":path})
    monkeypatch.setattr(impact,"search",lambda *a,**k:[cited])
    with pytest.raises(ValueError,match="template ownership"):
        impact.analyze(summary)


def test_missing_index_error_not_hidden(summary, monkeypatch):
    def missing(*a,**k):
        raise RuntimeError("Run python -m part2_knowledge.knowledge_base.ingest")
    monkeypatch.setattr(impact,"search",missing)
    with pytest.raises(RuntimeError,match="ingest"):
        impact.analyze(summary)


def test_duplicate_impacts_one_draft_and_sources_deduped(summary):
    report = impact.analyze(summary)
    duplicate = report.model_copy(update={"impacts":report.impacts + report.impacts})
    first = action_planner.plan(summary,duplicate)
    assert len(first) == 2
    assert len({s.model_dump_json() for s in first[0].sources}) == len(first[0].sources)
    assert first == action_planner.plan(summary,duplicate)


def test_planner_prompt_deduplicates_evidence_without_changing_saved_sources(summary,semantic_mocks):
    report = impact.analyze(summary)
    actions = action_planner.plan(summary,report)
    requests = [json.loads(user.split("\n",1)[1].rsplit("\n",1)[0])
                for _,user,schema in semantic_mocks["llm"] if schema is DraftAction]
    for request in requests:
        assert all("sources" not in i for i in request["impacts"])
        assert len({json.dumps(s,sort_keys=True) for s in request["sources"]}) == len(request["sources"])
        action = next(a for a in actions if a.unit_id == request["unit"]["unit_id"])
        assert request["sources"] == [s.model_dump(mode="json") for s in action.sources]


@pytest.mark.parametrize("field,value,error", [("change_id","FOREIGN","different change"),
    ("unit_id","CS-BSc","foreign unit"), ("requirement_id","UNKNOWN","unknown requirement"),
    ("stakeholders",["BANK-C"],"stakeholders")])
def test_planner_revalidates_report(summary, field, value, error):
    report = impact.analyze(summary)
    if field == "change_id":
        report = report.model_copy(update={field:value})
    else:
        report = report.model_copy(update={"impacts":[report.impacts[0].model_copy(update={field:value})]})
    with pytest.raises(ValueError,match=error):
        action_planner.plan(summary,report)


def test_unknown_due_date_needs_human_input_if_template_requires_it(summary):
    report = impact.analyze(summary)
    with pytest.raises(ValueError,match="due_before.*human input"):
        action_planner.plan(summary.model_copy(update={"effective_date":None}),report)


def test_optional_null_due_date_preserved(summary, monkeypatch):
    report = impact.analyze(summary)
    template = load_template(summary.template_id).model_copy(update={"action_item_fields":["title","checks"]})
    monkeypatch.setattr(action_planner,"load_template",lambda *a,**k:template)
    actions = action_planner.plan(summary.model_copy(update={"effective_date":None}),report)
    assert all(a.due_before is None for a in actions)


def test_unknown_template_required_field_error(summary, monkeypatch):
    report = impact.analyze(summary)
    template = load_template(summary.template_id).model_copy(update={"action_item_fields":["unavailable_field"]})
    monkeypatch.setattr(action_planner,"load_template",lambda *a,**k:template)
    with pytest.raises(ValueError,match="unavailable_field"):
        action_planner.plan(summary,report)


@pytest.mark.parametrize("field,value,error", [("description","Missing requirement references","cite every"),
    ("title"," ","must not be blank"), ("owner_role"," ","must not be blank"),
    ("checks",[{"steps":[" "],"expected":"done"}]*2,"nonblank")])
def test_bad_narrative_rejected(summary, monkeypatch, field, value, error):
    report = impact.analyze(summary)
    original = llm.complete_json
    def bad(system,user,schema):
        result = original(system,user,schema)
        return DraftAction.model_validate({**result.model_dump(),field:value})
    monkeypatch.setattr(llm,"complete_json",bad)
    with pytest.raises(ValueError,match=error):
        action_planner.plan(summary,report)


@pytest.mark.parametrize("count",[0,1,5])
def test_two_to_four_checks_enforced(count):
    payload = dict(DraftAction.model_config["json_schema_extra"]["example"])
    payload["checks"] = [{"steps":["Inspect policy"],"expected":"Policy complies"}]*count
    with pytest.raises(ValueError):
        DraftAction.model_validate(payload)


def test_planner_foreign_history_rejected(summary, monkeypatch):
    report = impact.analyze(summary)
    monkeypatch.setattr(action_planner,"search",lambda *a,**k:[source("university","CS-BSc","past_action_item")])
    with pytest.raises(ValueError,match="template ownership"):
        action_planner.plan(summary,report)


@pytest.mark.parametrize("name",["watcher","impact","action_planner"])
@pytest.mark.parametrize("template_id",["payments","university"])
def test_all_prompts_render_and_protect_untrusted_data(name,template_id):
    rendered = prompt(name,load_template(template_id))
    assert "untrusted data" in rendered and ("v1" in rendered or "v2" in rendered)


def test_eight_real_eval_cases_with_case_matched_mocks(semantic_mocks):
    report = quality_check.evaluate()
    assert len(report["cases"]) == 8
    assert report["overall"]["targets_met"]
    assert report["targets_met"] and all(r["targets_met"] for r in report["per_template"].values())
    assert report["interface_only"]  # Mock success is never real-model accuracy.


def test_quote_and_fact_metrics_do_not_count_retrieval(summary):
    doc = get_change(summary.change_id,template_id=summary.template_id)
    output = cli.run(doc)
    output["summary"]["summary_text"] = ""
    for r in output["summary"]["requirements"]:
        r["description"] = ""
        r["source_quote"] = "Invented quote"
    output["action_items"] = []
    output["impact_report"]["impacts"] = []
    metrics = quality_check.score_case({"expected_units":["ACH"],"expected_stakeholders":["BANK-A"],
                                        "expected_requirements_min":3,"key_facts":["BE04"]},doc,output)
    assert metrics["quote_validity"] == 0 and metrics["key_fact_coverage"] == 0


def test_cli_mocked_success_json(semantic_mocks,capsys):
    assert cli.main(["CHG-U-001","--template","university"]) == 0
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert len(output["action_items"]) == 2 and output["interface_only"]
    assert "FAKE PROVIDER" in captured.err


@pytest.mark.parametrize("args",[["UNKNOWN"],["CHG-P-002","--template","missing"],
                                 ["CHG-P-002","--template","university"]])
def test_cli_input_errors(args,capsys):
    assert cli.main(args) == 2
    assert "error" in capsys.readouterr().err


def test_cli_missing_index(summary,monkeypatch,capsys):
    monkeypatch.setattr(cli,"summarize",lambda doc:summary)
    def missing(summary):
        raise RuntimeError("missing collection")
    monkeypatch.setattr(cli,"analyze",missing)
    assert cli.main(["CHG-P-002"]) == 3
    assert "python -m part2_knowledge.knowledge_base.ingest" in capsys.readouterr().err


def test_cli_provider_failure(monkeypatch,capsys):
    def unavailable(doc):
        raise llm.LLMError("Groq credentials missing.")
    monkeypatch.setattr(cli,"summarize",unavailable)
    assert cli.main(["CHG-P-002"]) == 3
    assert "credentials missing" in capsys.readouterr().err


def test_live_evaluation_requires_explicit_flag(monkeypatch,capsys):
    from part2_knowledge.common.config import settings
    monkeypatch.setattr(settings,"llm_provider","groq")
    assert quality_check.main([]) == 2
    assert "LIVE GROQ QUALITY EVALUATION NOT RUN" in capsys.readouterr().err


def test_empty_evaluation_refused():
    with pytest.raises(ValueError,match="must not be empty"):
        quality_check.aggregate([])


@pytest.mark.parametrize("template_id,change_id,expected", [
    ("payments","CHG-P-002",{"ACH","IPS"}),
    ("university","CHG-U-001",{"CS-BSc","SE-BSc"})])
def test_real_chroma_search_with_mocked_llm(semantic_mocks,monkeypatch,tmp_path,template_id,change_id,expected):
    from part2_knowledge.common.config import settings
    from part2_knowledge.knowledge_base.ingest import ingest_all
    from part2_knowledge.knowledge_base.search import search
    monkeypatch.setattr(settings,"chroma_dir",tmp_path / "chroma")
    ingest_all(template_id=template_id)
    monkeypatch.setattr(impact,"search",search)
    monkeypatch.setattr(action_planner,"search",search)
    outputs = cli.run(get_change(change_id,template_id=template_id))
    assert {a["unit_id"] for a in outputs["action_items"]} == expected
    assert any(i["sources"] for i in outputs["impact_report"]["impacts"])
    assert all(s["metadata"]["template_id"] == template_id
               for i in outputs["impact_report"]["impacts"] for s in i["sources"])
