"""Human review rules: nothing reaches the action list or a person without a decision."""
from datetime import datetime, timezone
from uuid import uuid4

from contracts.schemas import ActionItem, Check, Investigation, ReviewDecision, Task
from part1_templates.tools.action_list import create_action_item
from part1_templates.tools.requests import set_request_status
from part1_templates.tools.templates import load_template
from part4_request_desk import orchestrator as orch
from part5_web.safety import audit


class ReviewError(ValueError):
    """The review request is invalid for this task or item."""


def review_items(task: Task) -> list[str]:
    """IDs a reviewer must decide on before the task is finished."""
    if task.type == "request":
        return [task.input_ref] if "investigation" in task.outputs else []
    items = task.outputs.get("action_items") or []
    return [item["action_id"] for item in items] or ([task.input_ref] if "summary" in task.outputs else [])


def _checks(value: object, original: list[Check]) -> list[Check]:
    if value is None:
        return original
    if not isinstance(value, list) or not 1 <= len(value) <= 6:
        raise ReviewError("Edited checks must be a list of 1 to 6 checks")
    checks = []
    for index, check in enumerate(value, 1):
        if not isinstance(check, dict):
            raise ReviewError("Each edited check must be an object with steps and expected")
        steps = [str(step).strip() for step in check.get("steps", []) if str(step).strip()]
        expected = str(check.get("expected", "")).strip()
        if not steps or not expected:
            raise ReviewError(f"Check {index} needs at least one step and an expected outcome")
        checks.append(Check(check_id=str(check.get("check_id") or f"C{index}"), steps=steps, expected=expected))
    return checks


def _decide_action(task: Task, item_id: str, decision: str, edited: object) -> str:
    items = [ActionItem.model_validate(item) for item in task.outputs.get("action_items") or []]
    index = next((i for i, item in enumerate(items) if item.action_id == item_id), None)
    if index is None:
        raise KeyError(f"Action item {item_id} not found in task {task.task_id}")
    item = items[index]
    if decision == "edit":
        if not isinstance(edited, dict):
            raise ReviewError("Editing an action item needs edited_content with description and/or checks")
        description = str(edited.get("description", item.description)).strip()
        if not description:
            raise ReviewError("The edited description must not be empty")
        item = item.model_copy(update={"description": description,
                                       "checks": _checks(edited.get("checks"), item.checks)})
    item = item.model_copy(update={"status": "rejected" if decision == "reject" else "approved"})
    items[index] = item
    if decision != "reject":  # save first: if Part 1 refuses, the task output stays unchanged
        create_action_item(item, template_id=task.template_id)  # Part 1 accepts approved items only
    orch.update_output(task.task_id, "action_items", items)
    return {"approve": "action_item_approved", "edit": "action_item_edited",
            "reject": "action_item_rejected"}[decision]


def _decide_reply(task: Task, decision: str, edited: object) -> list[str]:
    investigation = Investigation.model_validate(task.outputs["investigation"])
    if decision == "reject":
        return ["reply_rejected"]
    actions = []
    if decision == "edit":
        if not isinstance(edited, str) or not edited.strip():
            raise ReviewError("Editing a reply needs the new reply text in edited_content")
        investigation = investigation.model_copy(update={"draft_reply": edited.strip()})
        orch.update_output(task.task_id, "investigation", investigation)
        actions.append("reply_edited")
    set_request_status(task.input_ref, "answered", template_id=task.template_id)
    return actions + ["reply_sent"]


def apply_review(task_id: str, item_id: str, decision: str, reviewer: str,
                 edited_content: object = None, comment: str | None = None) -> ReviewDecision:
    """Validate, record and apply one human decision, then close the task when complete."""
    task = orch.get_task(task_id)
    template = load_template(task.template_id)
    if decision not in {"approve", "edit", "reject"}:
        raise ReviewError("decision must be approve, edit or reject")
    if reviewer not in template.reviewers:
        raise ReviewError(f"Reviewer must be one of: {', '.join(template.reviewers)}")
    if task.status != "pending_review":
        raise ReviewError(f"Task {task_id} is {task.status}; only pending_review tasks can be reviewed")
    if item_id not in review_items(task):
        raise KeyError(f"Item {item_id} is not reviewable in task {task_id}")
    comment = (comment or "").strip() or None
    if decision == "reject" and not comment:
        raise ReviewError("Rejecting needs a short comment")
    if any(d.item_id == item_id for d in audit.list_decisions(task_id)):
        raise ReviewError(f"Item {item_id} was already reviewed")

    if task.type == "request":
        actions = _decide_reply(task, decision, edited_content)
    elif item_id == task.input_ref:  # change with no action items: reviewer closes the summary
        actions = ["change_reviewed" if decision != "reject" else "change_rejected"]
    else:
        actions = [_decide_action(task, item_id, decision, edited_content)]

    saved = audit.save_decision(ReviewDecision(
        decision_id=f"RD-{uuid4().hex[:12]}", task_id=task_id, template_id=task.template_id,
        item_id=item_id, decision=decision, reviewer=reviewer,
        edited_content=edited_content if decision == "edit" else None, comment=comment,
        created_at=datetime.now(timezone.utc)))
    for action in actions:
        details = {"item_id": item_id, "comment": comment}
        if action == "reply_sent":
            details["mock"] = "nothing is really sent"
        audit.log_event(reviewer, action, task_id, details, template_id=task.template_id)

    decided = {d.item_id: d.decision for d in audit.list_decisions(task_id)}
    if set(review_items(task)) <= set(decided):
        status = "approved" if any(d != "reject" for d in decided.values()) else "rejected"
        orch.set_task_status(task_id, status)
        audit.log_event(reviewer, f"task_{status}", task_id, {}, template_id=task.template_id)
    return saved
