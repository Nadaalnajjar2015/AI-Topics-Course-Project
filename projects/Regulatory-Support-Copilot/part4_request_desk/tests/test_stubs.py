from pathlib import Path
import time

import pytest

from contracts.schemas import (
    ActionItem,
    ChangeDocument,
    ChangeSummary,
    ImpactReport,
    Investigation,
    Request,
    SearchResult,
    Task,
)
from part4_request_desk import investigator
from part1_templates.tools.templates import load_template
from part2_knowledge.common.config import settings
from part4_request_desk.orchestrator import (
    get_task,
    list_tasks,
    retry_task,
    run_change_sync,
    run_request_sync,
    set_task_status,
    start_change_task,
    start_request_task,
    update_output,
)
from part4_request_desk.orchestrator import orchestrator as orchestrator_module
from part4_request_desk.orchestrator import store


@pytest.fixture
def database_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    database = tmp_path / "runtime" / "tasks.db"
    monkeypatch.setattr(
        store,
        "settings",
        store.settings.model_copy(update={"app_db": database}),
    )
    return database


@pytest.fixture(autouse=True)
def fake_provider_and_knowledge(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "llm_provider", "fake")

    def fake_search(
        query: str,
        filters: dict[str, str],
        template_id: str,
        *,
        k: int = 2,
    ) -> list[SearchResult]:
        template = load_template(template_id)
        document_type = filters["doc_type"]
        reason_code = filters.get("reason_code")
        if document_type == "reason_codes":
            source = f"part1_templates/templates/{template_id}/{template.reason_codes_doc}"
            location = reason_code or "test-code"
            metadata = {"template_id": template_id, "reason_code": location}
        else:
            source = f"part1_templates/templates/{template_id}/history/past_requests.json"
            location = "similar-request"
            metadata = {"template_id": template_id}
        return [SearchResult(
            text="Fictional evidence for testing.",
            source=source,
            doc_type=document_type,
            location=location,
            score=0.9,
            metadata=metadata,
        )]

    monkeypatch.setattr(investigator, "_search_knowledge", fake_search)


def _request(request_id: str = "P-REQ-007", template_id: str = "payments") -> Request:
    example = Request.model_config["json_schema_extra"]["example"]
    return Request.model_validate(
        {**example, "request_id": request_id, "template_id": template_id}
    )


def _change() -> ChangeDocument:
    return ChangeDocument.model_validate(
        ChangeDocument.model_config["json_schema_extra"]["example"]
    )


def _patch_change_agents(monkeypatch: pytest.MonkeyPatch) -> None:
    summary = ChangeSummary.model_validate(
        ChangeSummary.model_config["json_schema_extra"]["example"]
    )
    impact = ImpactReport.model_validate(
        ImpactReport.model_config["json_schema_extra"]["example"]
    )
    action = ActionItem.model_validate(
        ActionItem.model_config["json_schema_extra"]["example"]
    )
    monkeypatch.setattr(orchestrator_module, "summarize", lambda _: summary)
    monkeypatch.setattr(orchestrator_module, "analyze", lambda _: impact)
    monkeypatch.setattr(orchestrator_module, "plan", lambda *_: [action])


def _wait_for_completion(task_id: str) -> Task:
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        task = get_task(task_id)
        if task.status != "running":
            return task
        time.sleep(0.01)
    return get_task(task_id)


def test_investigate_returns_investigation_example() -> None:
    request = _request()

    result = investigator.investigate(request)

    assert isinstance(result, Investigation)
    assert result.request_id == request.request_id
    assert result.item == "7731"
    assert result.reason_code == "AC04"


def test_sync_functions_return_finished_tasks_and_expected_outputs(
    database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_change_agents(monkeypatch)
    change_task = run_change_sync(_change())
    request_task = run_request_sync(_request())

    assert change_task.status == request_task.status == "pending_review"
    assert change_task.template_id == "payments"
    assert set(change_task.outputs) == {"summary", "impact_report", "action_items"}
    assert request_task.input_ref == "P-REQ-007"
    assert set(request_task.outputs) == {"investigation"}
    assert get_task(change_task.task_id) == change_task
    assert get_task(request_task.task_id) == request_task


def test_start_functions_save_fake_finished_tasks(
    database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_change_agents(monkeypatch)
    change_id = start_change_task(_change())
    request = _request("U-REQ-007", "university")
    request_id = start_request_task(request)

    change_task = _wait_for_completion(change_id)
    request_task = _wait_for_completion(request_id)
    assert change_task.status == "pending_review"
    assert change_task.type == "change"
    assert request_task.template_id == "university"
    assert request_task.input_ref == "U-REQ-007"


def test_list_status_and_output_updates_and_retry(database_path: Path) -> None:
    first = run_request_sync(_request())
    second = run_request_sync(_request("U-REQ-007", "university"))

    assert [task.task_id for task in list_tasks(template_id="university")] == [
        second.task_id
    ]
    assert [task.task_id for task in list_tasks(type="request")] == [
        second.task_id,
        first.task_id,
    ]

    set_task_status(first.task_id, "approved")
    update_output(first.task_id, "review_note", {"accepted": True})
    updated = get_task(first.task_id)
    assert updated.status == "approved"
    assert updated.outputs["review_note"] == {"accepted": True}

    retry_id = retry_task(first.task_id)
    retry = _wait_for_completion(retry_id)
    assert retry.task_id != first.task_id
    assert retry.input_ref == first.input_ref
    assert retry.type == first.type
    assert retry.status == "pending_review"
    assert set(retry.outputs) == {"investigation"}
