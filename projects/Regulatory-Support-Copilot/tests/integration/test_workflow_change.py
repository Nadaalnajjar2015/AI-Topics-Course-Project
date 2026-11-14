import pytest

from part1_templates.tools.changes import get_change
from part4_request_desk.orchestrator.orchestrator import run_change_sync


@pytest.mark.parametrize(
    ("template_id", "change_id"),
    [
        ("payments", "CHG-P-002"),
        ("university", "CHG-U-001"),
    ],
)
def test_change_workflow_finishes_with_all_outputs(
    template_id: str,
    change_id: str,
) -> None:
    document = get_change(change_id, template_id=template_id)

    task = run_change_sync(document)

    assert task.template_id == template_id
    assert task.type == "change"
    assert task.status == "pending_review"
    assert [step.status for step in task.steps] == ["done", "done", "done"]
    assert set(task.outputs) == {"summary", "impact_report", "action_items"}
    assert isinstance(task.outputs["summary"], dict)
    assert isinstance(task.outputs["impact_report"], dict)
    assert isinstance(task.outputs["action_items"], list)
    assert all(isinstance(item, dict) for item in task.outputs["action_items"])
