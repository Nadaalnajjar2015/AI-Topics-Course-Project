from pathlib import Path
from threading import Event, current_thread
import time

import pytest

from contracts.schemas import (
    ActionItem,
    ChangeDocument,
    ChangeSummary,
    ImpactReport,
    Investigation,
    Request,
    Task,
)
from part4_request_desk.orchestrator import orchestrator
from part4_request_desk.orchestrator import run, store


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


def test_sync_change_records_waiting_running_done_sequence(
    database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = ChangeSummary.model_validate(
        ChangeSummary.model_config["json_schema_extra"]["example"]
    )
    impact = ImpactReport.model_validate(
        ImpactReport.model_config["json_schema_extra"]["example"]
    )
    action = ActionItem.model_validate(
        ActionItem.model_config["json_schema_extra"]["example"]
    )
    monkeypatch.setattr(orchestrator, "summarize", lambda _: summary)
    monkeypatch.setattr(orchestrator, "analyze", lambda _: impact)
    monkeypatch.setattr(orchestrator, "plan", lambda *_: [action])

    saved_tasks: list[Task] = []
    save_task = orchestrator.save_task

    def record_save(task: Task) -> None:
        saved_tasks.append(task)
        save_task(task)

    monkeypatch.setattr(orchestrator, "save_task", record_save)
    events: list[str] = []
    monkeypatch.setattr(
        orchestrator,
        "_write_audit_event",
        lambda actor, action, task_id, details, template_id=None: events.append(action),
    )

    task = orchestrator.run_change_sync(_change())

    assert task.status == "pending_review"
    assert [step.status for step in task.steps] == ["done", "done", "done"]
    assert set(task.outputs) == {"summary", "impact_report", "action_items"}
    assert isinstance(task.outputs["summary"], dict)
    assert isinstance(task.outputs["impact_report"], dict)
    assert isinstance(task.outputs["action_items"], list)
    assert all(isinstance(item, dict) for item in task.outputs["action_items"])
    assert any(all(step.status == "waiting" for step in saved.steps) for saved in saved_tasks)
    assert any(saved.steps[0].status == "running" for saved in saved_tasks)
    assert events == ["task_created", "step_done", "step_done", "step_done"]


def test_failed_agent_marks_task_and_step_failed(
    database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(_: ChangeDocument) -> ChangeSummary:
        raise RuntimeError("agent failed clearly")

    monkeypatch.setattr(orchestrator, "summarize", fail)
    events: list[str] = []
    monkeypatch.setattr(
        orchestrator,
        "_write_audit_event",
        lambda actor, action, task_id, details, template_id=None: events.append(action),
    )

    task = orchestrator.run_change_sync(_change())

    assert task.status == "failed"
    assert task.steps[0].status == "failed"
    assert task.steps[0].error == "agent failed clearly"
    assert task.steps[0].message == "Change Watcher failed: agent failed clearly"
    assert [step.status for step in task.steps[1:]] == ["waiting", "waiting"]
    assert events == ["task_created", "step_failed"]
    assert orchestrator.get_task(task.task_id) == task


def test_retry_task_starts_a_new_request_task(
    database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    example = Investigation.model_config["json_schema_extra"]["example"]
    monkeypatch.setattr(
        orchestrator,
        "investigate",
        lambda request: Investigation.model_validate(
            {**example, "request_id": request.request_id}
        ),
    )
    original = orchestrator.run_request_sync(_request())

    retry_id = orchestrator.retry_task(original.task_id)

    assert retry_id != original.task_id
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        retry = orchestrator.get_task(retry_id)
        if retry.status != "running":
            break
        time.sleep(0.01)
    assert retry.status == "pending_review"
    assert retry.input_ref == original.input_ref
    assert retry.template_id == original.template_id
    assert set(retry.outputs) == {"investigation"}


def test_background_request_returns_before_agent_finishes(
    database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entered_agent = Event()
    release_agent = Event()
    agent_was_daemon: list[bool] = []

    def blocked_investigation(request: Request) -> Investigation:
        entered_agent.set()
        agent_was_daemon.append(current_thread().daemon)
        if not release_agent.wait(timeout=5):
            raise TimeoutError("test did not release the investigator")
        example = Investigation.model_config["json_schema_extra"]["example"]
        return Investigation.model_validate(
            {**example, "request_id": request.request_id}
        )

    monkeypatch.setattr(orchestrator, "investigate", blocked_investigation)
    started_at = time.monotonic()
    task_id = orchestrator.start_request_task(_request())
    elapsed = time.monotonic() - started_at

    try:
        assert elapsed < 1
        assert entered_agent.wait(timeout=2)
        task = orchestrator.get_task(task_id)
        assert task.status == "running"
        assert task.steps[0].status == "running"
        assert agent_was_daemon == [True]
    finally:
        release_agent.set()

    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        if orchestrator.get_task(task_id).status != "running":
            break
        time.sleep(0.01)
    assert orchestrator.get_task(task_id).status == "pending_review"


def test_tasks_remain_separated_by_template(
    database_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    example = Investigation.model_config["json_schema_extra"]["example"]
    monkeypatch.setattr(
        orchestrator,
        "investigate",
        lambda request: Investigation.model_validate(
            {**example, "request_id": request.request_id}
        ),
    )

    payments = orchestrator.run_request_sync(_request())
    university = orchestrator.run_request_sync(_request("U-REQ-007", "university"))

    assert [task.task_id for task in orchestrator.list_tasks(template_id="payments")] == [
        payments.task_id
    ]
    assert [task.task_id for task in orchestrator.list_tasks(template_id="university")] == [
        university.task_id
    ]


def test_cli_request_uses_template_override(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    request = _request("U-REQ-007", "university")
    task = Task.model_validate(
        {
            **Task.model_config["json_schema_extra"]["example"],
            "template_id": "university",
            "input_ref": "U-REQ-007",
        }
    )
    looked_up: list[tuple[str, str]] = []
    monkeypatch.setattr(
        run,
        "get_request",
        lambda request_id, template_id: (
            looked_up.append((request_id, template_id)) or request
        ),
    )
    monkeypatch.setattr(run, "run_request_sync", lambda _: task)
    monkeypatch.setattr(run, "_print_task", lambda _: None)

    assert run.main(["--request", "U-REQ-007", "--template", "university"]) == 0
    assert looked_up == [("U-REQ-007", "university")]
    assert capsys.readouterr().out == ""


def test_cli_change_uses_active_template_by_default(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    document = _change()
    task = Task.model_validate(
        {
            **Task.model_config["json_schema_extra"]["example"],
            "type": "change",
            "input_ref": document.change_id,
        }
    )
    looked_up: list[tuple[str, str]] = []
    monkeypatch.setattr(run.settings, "active_template", "payments")
    monkeypatch.setattr(
        run,
        "get_change",
        lambda change_id, template_id: (
            looked_up.append((change_id, template_id)) or document
        ),
    )
    monkeypatch.setattr(run, "run_change_sync", lambda _: task)
    monkeypatch.setattr(run, "_print_task", lambda _: None)

    assert run.main(["--change", document.change_id]) == 0
    assert looked_up == [(document.change_id, "payments")]
    assert capsys.readouterr().out == ""


def test_cli_list_filters_only_when_template_is_given(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    filters: list[str | None] = []
    monkeypatch.setattr(
        run,
        "list_tasks",
        lambda template_id: (filters.append(template_id) or []),
    )

    assert run.main(["--list"]) == 0
    assert run.main(["--list", "--template", "university"]) == 0

    assert filters == [None, "university"]
    assert capsys.readouterr().out == "[]\n[]\n"
