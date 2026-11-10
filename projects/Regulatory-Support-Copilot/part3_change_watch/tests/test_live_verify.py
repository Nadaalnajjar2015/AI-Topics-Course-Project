"""Verifier guard/rate-budget tests: entirely offline, no live calls in pytest."""
import json

import pytest

from part2_knowledge.common import llm
from part2_knowledge.common.config import settings
from part3_change_watch import live_verify


def test_spacing_and_restore(monkeypatch):
    sleeps = []
    def complete(*args):
        return "validated"
    monkeypatch.setattr(llm,"complete_json",complete)
    monkeypatch.setattr(live_verify.time,"monotonic",lambda:0)
    monkeypatch.setattr(live_verify.time,"sleep",sleeps.append)
    class Schema:
        pass
    with live_verify.limited_calls(15,2) as calls:
        assert llm.complete_json("","",Schema) == "validated"
        assert llm.complete_json("","",Schema) == "validated"
    assert len(calls) == 2 and sleeps == [15]
    assert llm.complete_json is complete


def test_rate_limits_have_bounded_retries(monkeypatch):
    sleeps = []
    def limited(*args):
        raise llm.LLMError("Groq request failed: rate limit exhausted.")
    monkeypatch.setattr(llm,"complete_json",limited)
    monkeypatch.setattr(live_verify.time,"sleep",sleeps.append)
    with live_verify.limited_calls(3,5,rate_retries=2) as calls:
        with pytest.raises(llm.LLMError,match="rate limit"):
            llm.complete_json("","",str)
    assert len(calls) == 3
    assert sleeps.count(30) == 2
    assert all(c["status"] == "rate_limited" for c in calls)


def test_semantic_failure_never_retried(monkeypatch):
    def invalid(*args):
        raise llm.LLMError("Groq JSON does not validate against the requested contract.")
    monkeypatch.setattr(llm,"complete_json",invalid)
    with live_verify.limited_calls(3,5) as calls:
        with pytest.raises(llm.LLMError,match="does not validate"):
            llm.complete_json("","",str)
    assert len(calls) == 1 and llm.complete_json is invalid


def test_call_budget(monkeypatch):
    monkeypatch.setattr(llm,"complete_json",lambda *args:None)
    with live_verify.limited_calls(3,1):
        llm.complete_json("","",str)
        with pytest.raises(llm.LLMError,match="budget exhausted"):
            llm.complete_json("","",str)


def test_absent_key_stops_before_any_call(monkeypatch,capsys):
    monkeypatch.setattr(settings,"groq_api_key","")
    monkeypatch.setattr(llm,"complete_json",lambda *args:pytest.fail("No credentials"))
    assert live_verify.main(["--allow-live"]) == 2
    assert "NOT RUN" in capsys.readouterr().out


def test_evaluation_requires_both_successful_same_model_smokes(monkeypatch,tmp_path):
    monkeypatch.setattr(live_verify,"PROJECT_ROOT",tmp_path)
    monkeypatch.setattr(settings,"groq_api_key","fictional-key")
    monkeypatch.setattr(llm,"complete_json",lambda *args:pytest.fail("Smoke gate required"))
    root = tmp_path / "runtime/part3_live"
    root.mkdir(parents=True)
    (root / "smoke.json").write_text(json.dumps({"completed":True,"model":"different-model","smoke":[]}),encoding="utf-8")
    assert live_verify.main(["--allow-live","--phase","evaluation"]) == 3
    report = json.loads((root / "evaluation.json").read_text(encoding="utf-8"))
    assert not report["completed"] and report["calls"] == []


def test_explicit_permission_flag_required():
    with pytest.raises(SystemExit):
        live_verify.main([])


def test_empty_smoke_cannot_unlock_evaluation():
    assert not live_verify.smoke_valid({"summary":{"requirements":[]},"impact_report":{"impacts":[]},"action_items":[]})


def test_completed_smoke_case_survives_another_case_failure(tmp_path):
    (tmp_path / "smoke.json").write_text(json.dumps({
        "provider":"groq","model":"test-model","completed":False,
        "smoke":[{"template_id":"payments","passed":True}],
    }),encoding="utf-8")
    (tmp_path / "smoke-university.json").write_text(json.dumps({
        "provider":"groq","model":"test-model","completed":True,
        "smoke":[{"template_id":"university","passed":True}],
    }),encoding="utf-8")
    passed = live_verify.successful_smokes(tmp_path,"test-model")
    assert set(passed) == {"payments","university"}
    assert not live_verify.successful_smokes(tmp_path,"different-model")


def test_failed_case_and_fake_report_never_unlock_evaluation(tmp_path):
    (tmp_path / "smoke.json").write_text(json.dumps({
        "provider":"groq","model":"test-model","smoke":[{"template_id":"payments","passed":False}],
    }),encoding="utf-8")
    (tmp_path / "smoke-university.json").write_text(json.dumps({
        "provider":"fake","model":"test-model","smoke":[{"template_id":"university","passed":True}],
    }),encoding="utf-8")
    assert not live_verify.successful_smokes(tmp_path,"test-model")
