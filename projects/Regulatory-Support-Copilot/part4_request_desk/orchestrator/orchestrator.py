"""Placeholder orchestrator APIs returning persisted, fake finished tasks."""

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel

from contracts.schemas import (
    ActionItem,
    ChangeDocument,
    ChangeSummary,
    ImpactReport,
    Request,
    Task,
    TaskStep,
)
from part4_request_desk.investigator import investigate

from .store import load_task, query_tasks, save_task

TaskStatus = Literal["running", "pending_review", "approved", "rejected", "failed"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_task_id() -> str:
    return f"T-{uuid4().hex}"


def _step(name: str, message: str) -> TaskStep:
    finished_at = _now()
    return TaskStep(
        name=name,
        status="done",
        started_at=finished_at,
        finished_at=finished_at,
        error=None,
        message=message,
    )


def _change_outputs() -> dict[str, object]:
    summary = ChangeSummary.model_validate(
        ChangeSummary.model_config["json_schema_extra"]["example"]
    )
    impact_report = ImpactReport.model_validate(
        ImpactReport.model_config["json_schema_extra"]["example"]
    )
    action_item = ActionItem.model_validate(
        ActionItem.model_config["json_schema_extra"]["example"]
    )
    return {
        "summary": summary.model_dump(mode="json"),
        "impact_report": impact_report.model_dump(mode="json"),
        "action_items": [action_item.model_dump(mode="json")],
    }


def _finished_change_task(doc: ChangeDocument) -> Task:
    return Task(
        task_id=_new_task_id(),
        template_id=doc.template_id,
        type="change",
        status="pending_review",
        input_ref=doc.change_id,
        steps=[
            _step("Change Watcher", "Fake change summary is ready."),
            _step("Impact Analyst", "Fake impact report is ready."),
            _step("Action Planner", "Fake action items are ready for review."),
        ],
        outputs=_change_outputs(),
        created_at=_now(),
    )


def _finished_request_task(request: Request) -> Task:
    investigation = investigate(request)
    return Task(
        task_id=_new_task_id(),
        template_id=request.template_id,
        type="request",
        status="pending_review",
        input_ref=request.request_id,
        steps=[
            _step("Request Investigator", "Fake investigation is ready for review.")
        ],
        outputs={"investigation": investigation.model_dump(mode="json")},
        created_at=_now(),
    )


def run_change_sync(doc: ChangeDocument) -> Task:
    """Create and persist a fake finished change task without a background thread."""
    task = _finished_change_task(doc)
    save_task(task)
    return task


def run_request_sync(request: Request) -> Task:
    """Create and persist a fake finished request task without a background thread."""
    task = _finished_request_task(request)
    save_task(task)
    return task


def start_change_task(doc: ChangeDocument) -> str:
    """Create a fake finished change task and return its ID."""
    return run_change_sync(doc).task_id


def start_request_task(request: Request) -> str:
    """Create a fake finished request task and return its ID."""
    return run_request_sync(request).task_id


def get_task(task_id: str) -> Task:
    """Return one stored task."""
    return load_task(task_id)


def list_tasks(
    template_id: str | None = None,
    type: str | None = None,
    status: str | None = None,
) -> list[Task]:
    """Return stored tasks matching the optional filters."""
    return query_tasks(template_id=template_id, type=type, status=status)


def set_task_status(task_id: str, status: TaskStatus) -> None:
    """Update a stored task's review status."""
    task = load_task(task_id)
    updated = Task.model_validate(
        {**task.model_dump(mode="json"), "status": status}
    )
    save_task(updated)


def _json_value(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def update_output(task_id: str, key: str, value: object) -> None:
    """Replace one output value on a stored task."""
    task = load_task(task_id)
    outputs = dict(task.outputs)
    outputs[key] = _json_value(value)
    updated = Task.model_validate(
        {**task.model_dump(mode="json"), "outputs": outputs}
    )
    save_task(updated)


def retry_task(task_id: str) -> str:
    """Create a fake completed retry using the stored task's input and outputs."""
    original = load_task(task_id)
    now = _now()
    retry = Task.model_validate(
        {
            **original.model_dump(mode="json"),
            "task_id": _new_task_id(),
            "status": "pending_review",
            "steps": [
                TaskStep(
                    name=step.name,
                    status="done",
                    started_at=now,
                    finished_at=now,
                    error=None,
                    message="Fake retry output copied from the previous task.",
                ).model_dump(mode="json")
                for step in original.steps
            ],
            "created_at": now.isoformat(),
        }
    )
    save_task(retry)
    return retry.task_id
