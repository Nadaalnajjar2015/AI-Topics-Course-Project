"""Runs change and request workflows and persists their task state."""

import logging
from datetime import datetime, timezone
from threading import Thread
from typing import Callable, Literal
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
from part1_templates.tools.changes import get_change
from part1_templates.tools.requests import get_request
from part4_request_desk.investigator import investigate

from .store import load_task, query_tasks, save_task

logger = logging.getLogger(__name__)
TaskStatus = Literal["running", "pending_review", "approved", "rejected", "failed"]

try:
    from part5_web.safety.audit import log_event as _write_audit_event
except ModuleNotFoundError as error:
    if error.name != "part5_web.safety.audit":
        raise

    def _write_audit_event(
        actor: str,
        action: str,
        task_id: str,
        details: dict[str, object],
        template_id: str | None = None,
    ) -> None:
        logger.info("Audit module unavailable; skipped %s for task %s.", action, task_id)


_StepOperation = tuple[str, str, Callable[[dict[str, object]], object]]


def summarize(doc: ChangeDocument) -> ChangeSummary:
    """Call the public Change Watcher API."""
    from part3_change_watch.watcher import summarize as run_summarize

    return run_summarize(doc)


def analyze(summary: ChangeSummary) -> ImpactReport:
    """Call the public Impact Analyst API."""
    from part3_change_watch.impact import analyze as run_analyze

    return run_analyze(summary)


def plan(summary: ChangeSummary, report: ImpactReport) -> list[ActionItem]:
    """Call the public Action Planner API."""
    from part3_change_watch.action_planner import plan as run_plan

    return run_plan(summary, report)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_task_id() -> str:
    return f"T-{uuid4().hex}"


def _json_value(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def _create_task(
    template_id: str,
    task_type: Literal["change", "request"],
    input_ref: str,
    step_names: list[str],
) -> Task:
    task = Task(
        task_id=_new_task_id(),
        template_id=template_id,
        type=task_type,
        status="running",
        input_ref=input_ref,
        steps=[
            TaskStep(
                name=name,
                status="waiting",
                started_at=None,
                finished_at=None,
                error=None,
                message=None,
            )
            for name in step_names
        ],
        outputs={},
        created_at=_now(),
    )
    save_task(task)
    _write_audit_event(
        actor="Orchestrator",
        action="task_created",
        task_id=task.task_id,
        details={"type": task.type, "input_ref": input_ref},
        template_id=template_id,
    )
    return task


def _run_steps(task: Task, operations: list[_StepOperation]) -> Task:
    for index, (name, output_key, operation) in enumerate(operations):
        started_at = _now()
        steps = list(task.steps)
        steps[index] = steps[index].model_copy(
            update={
                "status": "running",
                "started_at": started_at,
                "finished_at": None,
                "error": None,
                "message": f"{name} is running.",
            }
        )
        task = task.model_copy(update={"steps": steps})
        save_task(task)
        try:
            output = _json_value(operation(task.outputs))
        except Exception as error:
            finished_at = _now()
            steps = list(task.steps)
            steps[index] = steps[index].model_copy(
                update={
                    "status": "failed",
                    "finished_at": finished_at,
                    "error": str(error) or error.__class__.__name__,
                    "message": f"{name} failed.",
                }
            )
            task = task.model_copy(
                update={"steps": steps, "status": "failed"}
            )
            save_task(task)
            _write_audit_event(
                actor=name,
                action="step_failed",
                task_id=task.task_id,
                details={"error": task.steps[index].error or "Unknown error"},
                template_id=task.template_id,
            )
            return task

        outputs = dict(task.outputs)
        outputs[output_key] = output
        finished_at = _now()
        steps = list(task.steps)
        steps[index] = steps[index].model_copy(
            update={
                "status": "done",
                "finished_at": finished_at,
                "message": f"{name} completed.",
            }
        )
        task = task.model_copy(update={"steps": steps, "outputs": outputs})
        save_task(task)
        _write_audit_event(
            actor=name,
            action="step_done",
            task_id=task.task_id,
            details={"output_key": output_key, "message": task.steps[index].message},
            template_id=task.template_id,
        )

    task = task.model_copy(update={"status": "pending_review"})
    save_task(task)
    return task


def _change_operations(doc: ChangeDocument) -> list[_StepOperation]:
    return [
        ("Change Watcher", "summary", lambda _: summarize(doc)),
        (
            "Impact Analyst",
            "impact_report",
            lambda outputs: analyze(ChangeSummary.model_validate(outputs["summary"])),
        ),
        (
            "Action Planner",
            "action_items",
            lambda outputs: plan(
                ChangeSummary.model_validate(outputs["summary"]),
                ImpactReport.model_validate(outputs["impact_report"]),
            ),
        ),
    ]


def _request_operations(request: Request) -> list[_StepOperation]:
    return [
        (
            "Request Investigator",
            "investigation",
            lambda _: investigate(request),
        )
    ]


def _start_background(task: Task, operations: list[_StepOperation]) -> str:
    thread = Thread(target=_run_steps, args=(task, operations), daemon=True)
    thread.start()
    return task.task_id


def start_change_task(doc: ChangeDocument) -> str:
    """Persist a running change task and launch its steps on a daemon thread."""
    operations = _change_operations(doc)
    task = _create_task(
        doc.template_id,
        "change",
        doc.change_id,
        [operation[0] for operation in operations],
    )
    return _start_background(task, operations)


def start_request_task(request: Request) -> str:
    """Persist a running request task and launch investigation on a daemon thread."""
    operations = _request_operations(request)
    task = _create_task(
        request.template_id,
        "request",
        request.request_id,
        [operation[0] for operation in operations],
    )
    return _start_background(task, operations)


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
    """Start a new background task using the original input."""
    task = load_task(task_id)
    if task.type == "change":
        return start_change_task(
            get_change(task.input_ref, template_id=task.template_id)
        )
    return start_request_task(
        get_request(task.input_ref, template_id=task.template_id)
    )


def run_change_sync(doc: ChangeDocument) -> Task:
    """Run a change workflow synchronously for evaluation."""
    operations = _change_operations(doc)
    task = _create_task(
        doc.template_id,
        "change",
        doc.change_id,
        [operation[0] for operation in operations],
    )
    return _run_steps(task, operations)


def run_request_sync(request: Request) -> Task:
    """Run a request workflow synchronously for evaluation."""
    operations = _request_operations(request)
    task = _create_task(
        request.template_id,
        "request",
        request.request_id,
        [operation[0] for operation in operations],
    )
    return _run_steps(task, operations)
