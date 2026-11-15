"""Isolated fake-provider environment: temp task/audit DB, temp Part 1 state, fake search."""
import pytest
from fastapi.testclient import TestClient

from contracts.schemas import ActionItem, SearchResult, Task, TaskStep
from part1_templates.tools import _files
from part1_templates.tools.templates import load_template
from part2_knowledge.common.config import settings
from part2_knowledge.knowledge_base import search as search_module
from part3_change_watch import action_planner, impact
from part4_request_desk import investigator
from part4_request_desk.orchestrator import store


def fake_search(query, k=5, filters=None, template_id=None):
    template = load_template(template_id)
    doc_type = (filters or {}).get("doc_type", "document")
    if doc_type == "reason_codes":
        code = str((filters or {}).get("reason_code", ""))
        return [SearchResult(text=f"Fictional guidance for {code}.", doc_type="reason_codes", location=code,
                             source=f"part1_templates/templates/{template.id}/{template.reason_codes_doc}",
                             score=0.9, metadata={"template_id": template.id, "reason_code": code})][:k]
    if doc_type == "past_request":
        return [SearchResult(text="Similar fictional request.", doc_type="past_request", location="fixture",
                             source=f"part1_templates/templates/{template.id}/history/past_requests.json",
                             score=0.8, metadata={"template_id": template.id})][:k]
    return []


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "llm_provider", "fake")
    monkeypatch.setattr(settings, "active_template", "payments")
    monkeypatch.setattr(store, "settings", store.settings.model_copy(update={"app_db": tmp_path / "app.db"}))
    monkeypatch.setattr(_files, "_RUNTIME_ROOT", tmp_path / "runtime")
    monkeypatch.setattr(search_module, "search", fake_search)
    monkeypatch.setattr(impact, "search", fake_search)
    monkeypatch.setattr(action_planner, "search", fake_search)
    monkeypatch.setattr(investigator, "_search_knowledge",
                        lambda query, filters, template_id, *, k=2: fake_search(query, k, filters, template_id))
    return tmp_path


@pytest.fixture
def client():
    from part5_web.app import app
    return TestClient(app)


@pytest.fixture
def sync_tasks(monkeypatch):
    """Run workflows synchronously so tests see the finished task immediately."""
    from part4_request_desk import orchestrator as orch
    monkeypatch.setattr(orch, "start_request_task", lambda request: orch.run_request_sync(request).task_id)
    monkeypatch.setattr(orch, "start_change_task", lambda doc: orch.run_change_sync(doc).task_id)


@pytest.fixture
def change_task():
    """A finished payments change task with two draft action items awaiting review."""
    example = ActionItem.model_config["json_schema_extra"]["example"]
    second = {**example, "action_id": "AI-CHG-P-002-IPS", "unit_id": "IPS", "title": "Require addresses in IPS",
              "stakeholders": []}
    task = Task(task_id="T-test-change", template_id="payments", type="change", status="pending_review",
                input_ref="CHG-P-002",
                steps=[TaskStep(name=n, status="done", started_at=None, finished_at=None, error=None, message=None)
                       for n in ("Change Watcher", "Impact Analyst", "Action Planner")],
                outputs={"summary": {"change_id": "CHG-P-002", "template_id": "payments", "title": "t", "scope": "all",
                                     "effective_date": None, "summary_text": "s", "requirements": []},
                         "impact_report": {"change_id": "CHG-P-002", "impacts": [], "unmatched_requirements": []},
                         "action_items": [example, second]},
                created_at="2026-03-02T10:00:00")
    store.save_task(task)
    return task
