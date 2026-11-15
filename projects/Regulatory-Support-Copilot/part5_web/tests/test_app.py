import time

import pytest

from part1_templates.tools.action_list import list_action_items
from part1_templates.tools.requests import get_request
from part4_request_desk import orchestrator as orch
from part5_web.safety import audit

PAGES = ["/", "/changes/new", "/requests", "/action-items", "/audit", "/search", "/search?q=reason",
         "/setup", "/evaluation"]


@pytest.mark.parametrize("template_id", ["payments", "university"])
@pytest.mark.parametrize("path", PAGES)
def test_every_page_ok_for_both_templates(client, template_id, path):
    client.cookies.set("template_id", template_id)
    response = client.get(path)
    assert response.status_code == 200
    assert "Prototype – mock data" in response.text


def test_switcher_changes_organization_and_labels(client):
    page = client.get("/switch?template_id=university&next=/requests", follow_redirects=True)
    assert page.status_code == 200
    assert "Northfield University" in page.text and "Student requests" in page.text
    for payment_word in ("Cedar Payment Systems</span>", "Bank support ticket", "Client bank"):
        assert payment_word not in page.text
    setup = client.get("/setup")
    assert "Study programs" in setup.text and "registration_lookup" in setup.text
    back = client.get("/switch?template_id=payments&next=/setup", follow_redirects=True)
    assert "Product modules" in back.text and "transaction_lookup" in back.text


def test_switch_rejects_unknown_template_and_open_redirect(client):
    assert client.get("/switch?template_id=nope").status_code == 404
    response = client.get("/switch?template_id=payments&next=//evil.example", follow_redirects=False)
    assert response.headers["location"] == "/"


def test_reviewer_picker_only_accepts_template_reviewers(client):
    assert client.get("/reviewer?name=Registrar").status_code == 400  # payments reviewers only
    page = client.get("/reviewer?name=Support%20engineer&next=/", follow_redirects=True)
    assert '<option value="Support engineer" selected>' in page.text


@pytest.mark.parametrize(("method", "url", "body", "status"), [
    ("get", "/api/tasks/T-missing", None, 404),
    ("post", "/api/tasks/request", {"template_id": "payments", "request_id": "P-REQ-999"}, 404),
    ("post", "/api/tasks/request", {"template_id": "payments", "request_id": "U-REQ-007"}, 400),
    ("post", "/api/tasks/request", {"template_id": "nowhere", "request_id": "P-REQ-007"}, 404),
    ("post", "/api/tasks/change", {"template_id": "payments", "change_id": "CHG-X-404"}, 404),
    ("post", "/api/tasks/change", {"template_id": "payments", "change_id": "CHG-U-001"}, 400),
    ("post", "/api/tasks/change", {"template_id": "payments", "text": "   "}, 400),
    ("post", "/api/tasks/change", {"template_id": "payments", "text": "no header"}, 400),
    ("post", "/api/tasks/T-missing/review", {"item_id": "x", "decision": "approve"}, 404),
    ("get", "/api/search?q=AC04&template_id=nowhere", None, 404),
])
def test_api_validates_input(client, method, url, body, status):
    response = getattr(client, method)(url, json=body) if body is not None else getattr(client, method)(url)
    assert response.status_code == status
    assert response.json()["detail"]


def test_review_decision_must_be_known(client, change_task):
    response = client.post(f"/api/tasks/{change_task.task_id}/review",
                           json={"item_id": "AI-CHG-P-002-ACH", "decision": "send"})
    assert response.status_code == 400


def test_no_action_item_before_approval_then_approve_creates_it(client, change_task):
    assert list_action_items("payments") == []  # human-approval rule
    response = client.post(f"/api/tasks/{change_task.task_id}/review",
                           json={"item_id": "AI-CHG-P-002-ACH", "decision": "approve"})
    assert response.status_code == 200 and response.json()["reviewer"] == "Business analyst"
    saved = list_action_items("payments")
    assert [a.action_id for a in saved] == ["AI-CHG-P-002-ACH"] and saved[0].status == "approved"
    assert orch.get_task(change_task.task_id).status == "pending_review"  # one item still open
    assert "action_item_approved" in [e.action for e in audit.list_events(task_id=change_task.task_id)]
    page = client.get("/action-items")
    assert "AI-CHG-P-002-ACH" in page.text


def test_reject_requires_comment_and_closes_task(client, change_task):
    url = f"/api/tasks/{change_task.task_id}/review"
    assert client.post(url, json={"item_id": "AI-CHG-P-002-IPS", "decision": "reject"}).status_code == 400
    assert client.post(url, json={"item_id": "AI-CHG-P-002-IPS", "decision": "reject",
                                  "comment": "IPS not affected"}).status_code == 200
    edited = client.post(url, json={"item_id": "AI-CHG-P-002-ACH", "decision": "edit",
                                    "edited_content": {"description": "Edited by analyst",
                                                       "checks": [{"steps": ["Send one"], "expected": "BE04"}]}})
    assert edited.status_code == 200
    task = orch.get_task(change_task.task_id)
    assert task.status == "approved"
    items = {i["action_id"]: i for i in task.outputs["action_items"]}
    assert items["AI-CHG-P-002-IPS"]["status"] == "rejected"
    assert items["AI-CHG-P-002-ACH"]["description"] == "Edited by analyst"
    assert [a.action_id for a in list_action_items("payments")] == ["AI-CHG-P-002-ACH"]
    actions = [e.action for e in audit.list_events(task_id=change_task.task_id)]
    assert {"action_item_rejected", "action_item_edited", "task_approved"} <= set(actions)
    again = client.post(url, json={"item_id": "AI-CHG-P-002-ACH", "decision": "approve"})
    assert again.status_code == 400  # already finished


def test_all_rejected_task_is_rejected(client, change_task):
    url = f"/api/tasks/{change_task.task_id}/review"
    for item in ("AI-CHG-P-002-ACH", "AI-CHG-P-002-IPS"):
        client.post(url, json={"item_id": item, "decision": "reject", "comment": "no"})
    assert orch.get_task(change_task.task_id).status == "rejected"
    assert list_action_items("payments") == []


def test_request_flow_from_browser_to_answered(client, sync_tasks):
    response = client.post("/requests/P-REQ-007/investigate", follow_redirects=False)
    assert response.status_code == 303
    task_id = response.headers["location"].rsplit("/", 1)[1]
    page = client.get(f"/tasks/{task_id}")
    assert page.status_code == 200 and "AC04" in page.text and "Approve" in page.text
    assert get_request("P-REQ-007", "payments").status == "open"  # nothing sent before approval
    client.cookies.set("reviewer", "Support engineer")
    decision = client.post(f"/api/tasks/{task_id}/review", json={"item_id": "P-REQ-007", "decision": "approve"})
    assert decision.status_code == 200
    assert get_request("P-REQ-007", "payments").status == "answered"
    assert orch.get_task(task_id).status == "approved"
    assert "reply_sent" in [e.action for e in audit.list_events(task_id=task_id)]


def test_university_request_and_edited_reply(client, sync_tasks):
    client.get("/switch?template_id=university")
    task_id = client.post("/api/tasks/request", json={"request_id": "U-REQ-007"}).json()["task_id"]
    task = client.get(f"/api/tasks/{task_id}").json()
    assert task["template_id"] == "university"
    assert task["outputs"]["investigation"]["reason_code"] == "PREREQ_MISSING"
    url = f"/api/tasks/{task_id}/review"
    assert client.post(url, json={"item_id": "U-REQ-007", "decision": "edit", "edited_content": ""}).status_code == 400
    ok = client.post(url, json={"item_id": "U-REQ-007", "decision": "edit", "reviewer": "Registrar",
                                "edited_content": "Please complete SE201 first. Registrar's Office"})
    assert ok.status_code == 200
    assert orch.get_task(task_id).outputs["investigation"]["draft_reply"].startswith("Please complete SE201")
    assert get_request("U-REQ-007", "university").status == "answered"
    assert {"reply_edited", "reply_sent"} <= {e.action for e in audit.list_events(task_id=task_id)}
    assert client.get(f"/api/tasks?template_id=university&status=approved").json()[0]["task_id"] == task_id


def test_change_task_from_form_and_dashboard(client, sync_tasks):
    response = client.post("/changes/analyze", data={"change_id": "CHG-P-002", "text": ""}, follow_redirects=True)
    assert response.status_code == 200 and "Change Watcher" in response.text
    assert "CHG-P-002" in client.get("/").text
    empty = client.post("/changes/analyze", data={"change_id": "", "text": "not a document"})
    assert "YAML header" in empty.text


def test_failed_task_shows_error_and_retry_works(client, monkeypatch, sync_tasks):
    from part4_request_desk import investigator
    def broken(request):
        raise RuntimeError("model unavailable")
    monkeypatch.setattr(orch.orchestrator, "investigate", broken)
    task_id = client.post("/api/tasks/request", json={"request_id": "P-REQ-007"}).json()["task_id"]
    page = client.get(f"/tasks/{task_id}")
    assert "model unavailable" in page.text and "Retry" in page.text
    monkeypatch.setattr(orch.orchestrator, "investigate", investigator.investigate)
    retried = client.post(f"/tasks/{task_id}/retry", follow_redirects=False)
    new_id = retried.headers["location"].rsplit("/", 1)[1]
    assert new_id != task_id
    deadline = time.monotonic() + 10  # retry_task runs in Part 4's background thread
    while orch.get_task(new_id).status == "running" and time.monotonic() < deadline:
        time.sleep(0.05)
    assert orch.get_task(new_id).status == "pending_review"
    assert client.post(f"/api/tasks/{new_id}/retry").status_code == 400  # only failed tasks


def test_search_and_audit_api_are_template_scoped(client):
    results = client.get("/api/search?q=closed&doc_type=reason_codes&template_id=university").json()
    assert results and all(r["metadata"]["template_id"] == "university" for r in results)
    audit.log_event("x", "y", "T-9", {}, template_id="university")
    assert client.get("/api/audit?template_id=payments").json() == []
    assert len(client.get("/api/audit?template_id=university").json()) == 1
    assert {t["id"] for t in client.get("/api/templates").json()} == {"payments", "university"}


def test_pages_escape_untrusted_text(client, change_task):
    task = orch.get_task(change_task.task_id)
    items = task.outputs["action_items"]
    items[0]["description"] = "<script>alert(1)</script>"
    orch.update_output(task.task_id, "action_items", items)
    page = client.get(f"/tasks/{task.task_id}")
    assert "<script>alert(1)</script>" not in page.text and "&lt;script&gt;" in page.text


def test_request_list_and_task_page_mask_account_numbers(client, sync_tasks):
    page = client.get("/requests")
    assert "0013100030212" not in page.text and "*********0212" in page.text
    task_id = client.post("/api/tasks/request", json={"request_id": "P-REQ-002"}).json()["task_id"]
    task_page = client.get(f"/tasks/{task_id}")
    assert "Original bank support ticket" in task_page.text and "0013100030212" not in task_page.text
    assert "View result" in client.get("/requests").text
