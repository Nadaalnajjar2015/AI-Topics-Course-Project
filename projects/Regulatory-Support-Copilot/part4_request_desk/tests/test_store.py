from pathlib import Path

import pytest

from contracts.schemas import Task
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


def _task(
    task_id: str,
    *,
    template_id: str = "payments",
    task_type: str = "request",
    status: str = "pending_review",
    created_at: str = "2026-03-02T10:00:00",
) -> Task:
    example = Task.model_config["json_schema_extra"]["example"]
    return Task.model_validate(
        {
            **example,
            "task_id": task_id,
            "template_id": template_id,
            "type": task_type,
            "status": status,
            "created_at": created_at,
        }
    )


def test_save_and_load_task_round_trip(database_path: Path) -> None:
    task = _task("T-round-trip")

    store.save_task(task)

    assert database_path.exists()
    assert store.load_task(task.task_id) == task


def test_load_task_raises_for_unknown_id(database_path: Path) -> None:
    with pytest.raises(KeyError, match="T-missing"):
        store.load_task("T-missing")


def test_query_tasks_filters_template_type_and_status(database_path: Path) -> None:
    tasks = [
        _task("T-payments-request", created_at="2026-03-02T10:00:00"),
        _task(
            "T-university-request",
            template_id="university",
            created_at="2026-03-02T11:00:00",
        ),
        _task(
            "T-payments-change",
            task_type="change",
            created_at="2026-03-02T12:00:00",
        ),
        _task(
            "T-payments-failed",
            status="failed",
            created_at="2026-03-02T13:00:00",
        ),
    ]
    for task in tasks:
        store.save_task(task)

    assert [task.task_id for task in store.query_tasks(template_id="payments")] == [
        "T-payments-failed",
        "T-payments-change",
        "T-payments-request",
    ]
    assert [task.task_id for task in store.query_tasks(type="change")] == [
        "T-payments-change"
    ]
    assert [task.task_id for task in store.query_tasks(status="failed")] == [
        "T-payments-failed"
    ]
    assert [
        task.task_id
        for task in store.query_tasks(
            template_id="payments",
            type="request",
            status="pending_review",
        )
    ] == ["T-payments-request"]


def test_query_tasks_returns_newest_first(database_path: Path) -> None:
    for task in (
        _task("T-old", created_at="2026-03-02T09:00:00"),
        _task("T-new", created_at="2026-03-02T11:00:00"),
        _task("T-middle", created_at="2026-03-02T10:00:00"),
    ):
        store.save_task(task)

    assert [task.task_id for task in store.query_tasks()] == [
        "T-new",
        "T-middle",
        "T-old",
    ]
