from pathlib import Path

import pytest

from contracts.schemas import ChangeDocument, Investigation, Request, Task
from part4_request_desk import investigator
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


def _request(request_id: str = "P-REQ-007", template_id: str = "payments") -> Request:
    example = Request.model_config["json_schema_extra"]["example"]
    return Request.model_validate(
        {**example, "request_id": request_id, "template_id": template_id}
    )


def _change() -> ChangeDocument:
    return ChangeDocument.model_validate(
        ChangeDocument.model_config["json_schema_extra"]["example"]
    )


def test_investigate_returns_investigation_example() -> None:
    request = _request()

    result = investigator.investigate(request)

    assert isinstance(result, Investigation)
    assert result.request_id == request.request_id
    assert result.item == "7731"
    assert result.reason_code == "AC04"


def test_sync_functions_return_finished_tasks_and_expected_outputs(
    database_path: Path,
) -> None:
    change_task = run_change_sync(_change())
    request_task = run_request_sync(_request())

    assert change_task.status == request_task.status == "pending_review"
    assert change_task.template_id == "payments"
    assert set(change_task.outputs) == {"summary", "impact_report", "action_items"}
    assert request_task.input_ref == "P-REQ-007"
    assert set(request_task.outputs) == {"investigation"}
    assert get_task(change_task.task_id) == change_task
    assert get_task(request_task.task_id) == request_task


def test_start_functions_save_fake_finished_tasks(database_path: Path) -> None:
    change_id = start_change_task(_change())
    request = _request("U-REQ-007", "university")
    request_id = start_request_task(request)

    assert get_task(change_id).status == "pending_review"
    assert get_task(change_id).type == "change"
    assert get_task(request_id).template_id == "university"
    assert get_task(request_id).input_ref == "U-REQ-007"


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
    retry = get_task(retry_id)
    assert retry.task_id != first.task_id
    assert retry.input_ref == first.input_ref
    assert retry.type == first.type
    assert retry.status == "pending_review"
    assert retry.outputs == updated.outputs
