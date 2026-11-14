import pytest

from part1_templates.tools.requests import get_request
from part4_request_desk.orchestrator.orchestrator import run_request_sync


@pytest.mark.parametrize(
    ("template_id", "request_id", "item", "reason_code"),
    [
        ("payments", "P-REQ-007", "7731", "AC04"),
        ("university", "U-REQ-007", "SE301", "PREREQ_MISSING"),
    ],
)
def test_request_workflow_finishes_with_investigation_output(
    template_id: str,
    request_id: str,
    item: str,
    reason_code: str,
) -> None:
    request = get_request(request_id, template_id=template_id)

    task = run_request_sync(request)

    assert task.template_id == template_id
    assert task.type == "request"
    assert task.status == "pending_review"
    assert [step.status for step in task.steps] == ["done"]
    assert set(task.outputs) == {"investigation"}
    investigation = task.outputs["investigation"]
    assert isinstance(investigation, dict)
    assert investigation["request_id"] == request_id
    assert investigation["item"] == item
    assert investigation["reason_code"] == reason_code
    assert investigation["evidence"]
    assert investigation["sources"]
