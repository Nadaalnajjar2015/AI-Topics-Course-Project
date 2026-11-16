import sqlite3
from datetime import datetime, timezone

import pytest

from contracts.schemas import AuditEvent, ReviewDecision
from part5_web.safety import audit


def _decision(item_id="P-REQ-007", task_id="T-1", decision="approve", comment=None):
    return ReviewDecision(decision_id=f"RD-{item_id}-{task_id}", task_id=task_id, template_id="payments",
                          item_id=item_id, decision=decision, reviewer="Support engineer", edited_content=None,
                          comment=comment, created_at=datetime.now(timezone.utc))


def test_contract_examples_validate():
    for model in (AuditEvent, ReviewDecision):
        model.model_validate(model.model_config["json_schema_extra"]["example"])


def test_events_saved_with_template_and_listed_newest_first():
    audit.log_event("Orchestrator", "task_created", "T-1", {"x": 1}, template_id="payments")
    audit.log_event("Registrar", "reply_sent", "T-2", {}, template_id="university")
    audit.log_event("Orchestrator", "step_done", "T-1", {}, template_id="payments")
    events = audit.list_events(template_id="payments")
    assert [e.action for e in events] == ["step_done", "task_created"]
    assert all(e.template_id == "payments" for e in events)
    assert [e.action for e in audit.list_events(task_id="T-2")] == ["reply_sent"]
    assert len(audit.list_events()) == 3


def test_event_details_are_masked():
    audit.log_event("x", "y", "T-1", {"note": "acct 0013100030212", "nested": ["a.b@x.example"]}, "payments")
    details = audit.list_events()[0].details
    assert details == {"note": "acct *********0212", "nested": ["a***@x.example"]}


def test_log_event_never_raises(monkeypatch):
    monkeypatch.setattr(audit, "_connection", lambda: (_ for _ in ()).throw(sqlite3.OperationalError("disk")))
    audit.log_event("x", "y", "T-1", {"bad": object()})  # no exception


def test_events_are_append_only():
    audit.log_event("x", "y", "T-1", {})
    with pytest.raises(sqlite3.DatabaseError), audit._connection() as connection:
        connection.execute("DELETE FROM audit_events")
    assert len(audit.list_events()) == 1


def test_decisions_saved_listed_and_unique():
    audit.save_decision(_decision("A"))
    audit.save_decision(_decision("B", decision="reject", comment="wrong unit"))
    audit.save_decision(_decision("A", task_id="T-other"))
    assert [d.item_id for d in audit.list_decisions("T-1")] == ["A", "B"]
    assert audit.list_decisions("T-1")[1].comment == "wrong unit"
    with pytest.raises(ValueError):
        audit.save_decision(_decision("A"))
