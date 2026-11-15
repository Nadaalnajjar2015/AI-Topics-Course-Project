"""HTML pages. Every organization word comes from the active template's labels."""
import json
from collections import Counter

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from part1_templates.tools.action_list import list_action_items
from part1_templates.tools.changes import get_change, list_changes
from part1_templates.tools.directory import list_stakeholders, list_units
from part1_templates.tools.requests import get_request, list_requests
from part2_knowledge.common.config import PROJECT_ROOT, settings
from part4_request_desk import orchestrator as orch
from part5_web import api, review
from part5_web.context import (REVIEWER_COOKIE, TEMPLATE_COOKIE, active_template, find_task,
                               get_template, page)
from part5_web.safety import audit

router = APIRouter()
EVAL_REPORT = PROJECT_ROOT / "runtime" / "eval" / "report.json"
DOC_TYPES = ["document", "reason_codes", "unit", "stakeholder", "past_request", "past_action_item", "change"]


def _safe_next(target: str | None) -> str:
    return target if target and target.startswith("/") and not target.startswith("//") else "/"


def _redirect_to_task(task_id: str) -> RedirectResponse:
    return RedirectResponse(f"/tasks/{task_id}", status_code=303)


def _latest_tasks(template_id: str, type_: str) -> dict:
    """Newest task per input (request or change ID), so lists can link to existing results."""
    latest: dict = {}
    for task in sorted(orch.list_tasks(template_id=template_id, type=type_), key=lambda t: t.created_at):
        latest[task.input_ref] = task
    return latest


def _titles(template_id: str) -> dict[str, str]:
    """Human title for every request and change ID (used in the overview list)."""
    titles = {r.request_id: f"{r.person_id}: {r.subject}" for r in list_requests(template_id)}
    titles.update({c.change_id: c.title for c in list_changes(template_id)})
    return titles


def _source_of(task):
    """The original request or change a task was started from, or None for a pasted document."""
    try:
        if task.type == "request":
            return get_request(task.input_ref, task.template_id)
        return get_change(task.input_ref, task.template_id)
    except Exception:  # noqa: BLE001 - pasted documents have no stored source
        return None


def indexed_chunks(template_id: str) -> int | None:
    """Chunks in the template's collection, or None when the index was never built."""
    try:
        from part2_knowledge.knowledge_base import _store
        return _store._client().get_collection(f"kb_{template_id}").count()
    except Exception:  # noqa: BLE001 - missing index or Chroma unavailable
        return None


@router.get("/switch")
def switch_template(template_id: str, next: str | None = None):
    template = get_template(template_id)
    response = RedirectResponse(_safe_next(next), status_code=303)
    response.set_cookie(TEMPLATE_COOKIE, template.id, samesite="lax")
    response.delete_cookie(REVIEWER_COOKIE)  # reviewer roles differ per template
    return response


@router.get("/reviewer")
def switch_reviewer(request: Request, name: str, next: str | None = None):
    template = active_template(request)
    if name not in template.reviewers:
        raise HTTPException(400, f"Reviewer must be one of: {', '.join(template.reviewers)}")
    response = RedirectResponse(_safe_next(next), status_code=303)
    response.set_cookie(REVIEWER_COOKIE, name, samesite="lax")
    return response


@router.get("/")
def dashboard(request: Request):
    template = active_template(request)
    tasks = orch.list_tasks(template_id=template.id)
    counts = Counter(task.status for task in tasks)
    return page(request, "dashboard.html", template, tasks=tasks, counts=counts, titles=_titles(template.id))


@router.get("/changes/new")
def new_change(request: Request, error: str | None = None):
    template = active_template(request)
    return page(request, "change_new.html", template, changes=list_changes(template.id), error=error,
                latest=_latest_tasks(template.id, "change"))


@router.post("/changes/analyze")
def analyze_change(request: Request, change_id: str = Form(""), text: str = Form("")):
    pasted = text if text.strip() else None
    try:
        task_id = api.start_change(request, api.ChangeTaskBody(change_id=change_id or None, text=pasted))
    except HTTPException as error:
        template = active_template(request)
        return page(request, "change_new.html", template, changes=list_changes(template.id),
                    error=error.detail, pasted=text, latest=_latest_tasks(template.id, "change"))
    return _redirect_to_task(task_id)


@router.get("/requests")
def requests_page(request: Request):
    template = active_template(request)
    return page(request, "requests.html", template, requests=list_requests(template.id),
                latest=_latest_tasks(template.id, "request"))


@router.post("/requests/{request_id}/investigate")
def investigate(request: Request, request_id: str):
    return _redirect_to_task(api.start_request(request, api.RequestTaskBody(request_id=request_id)))


@router.get("/tasks/{task_id}")
def task_page(request: Request, task_id: str):
    task = find_task(task_id)
    template = get_template(task.template_id)  # a task always shows its own organization
    decisions = {d.item_id: d for d in audit.list_decisions(task_id)}
    return page(request, "task.html", template, task=task, decisions=decisions,
                review_items=review.review_items(task), source=_source_of(task))


@router.post("/tasks/{task_id}/retry")
def retry(task_id: str):
    return _redirect_to_task(api.do_retry(task_id))


@router.get("/action-items")
def action_items(request: Request):
    template = active_template(request)
    return page(request, "action_items.html", template, items=list_action_items(template.id))


@router.get("/audit")
def audit_page(request: Request, task_id: str = ""):
    template = active_template(request)
    events = audit.list_events(task_id=task_id.strip() or None, template_id=template.id, limit=500)
    return page(request, "audit.html", template, events=events, task_id=task_id.strip())


@router.get("/search")
def search_page(request: Request, q: str = "", doc_type: str = ""):
    template = active_template(request)
    results, error = [], None
    if q.strip():
        try:
            results = api.run_search(request, q, doc_type or None, template.id)
        except HTTPException as exc:
            error = exc.detail
    return page(request, "search.html", template, q=q, doc_type=doc_type, doc_types=DOC_TYPES,
                results=results, error=error)


@router.get("/setup")
def setup_page(request: Request):
    template = active_template(request)
    documents = sorted(p.name for p in (settings.templates_dir / template.id / "documents").glob("*.md"))
    return page(request, "setup.html", template, units=list_units(template.id),
                stakeholders=list_stakeholders(template.id), documents=documents,
                chunks=indexed_chunks(template.id))


@router.get("/evaluation")
def evaluation_page(request: Request):
    template = active_template(request)
    report = None
    if EVAL_REPORT.exists():
        try:
            report = json.loads(EVAL_REPORT.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            report = None
    return page(request, "evaluation.html", template, report=report)
