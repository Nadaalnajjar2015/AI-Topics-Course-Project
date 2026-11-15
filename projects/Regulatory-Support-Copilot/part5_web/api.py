"""JSON API used by the page JavaScript and the tests. Every call works on one template."""
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from contracts.schemas import AuditEvent, ReviewDecision, SearchResult, Task, TemplateConfig
from part1_templates.tools.templates import list_templates
from part2_knowledge.knowledge_base import ingest, search as search_module
from part4_request_desk import orchestrator as orch
from part5_web import review
from part5_web.context import active_reviewer, active_template, find_change, find_request, find_task
from part5_web.safety import audit

router = APIRouter(prefix="/api")


class ChangeTaskBody(BaseModel):
    template_id: str | None = None
    change_id: str | None = None
    text: str | None = None


class RequestTaskBody(BaseModel):
    template_id: str | None = None
    request_id: str = Field(min_length=1)


class ReviewBody(BaseModel):
    item_id: str = Field(min_length=1)
    decision: Literal["approve", "edit", "reject"]
    edited_content: dict[str, object] | str | None = None
    comment: str | None = Field(default=None, max_length=2000)
    reviewer: str | None = None


class RebuildBody(BaseModel):
    template_id: str | None = None


def start_change(request: Request, body: ChangeTaskBody) -> str:
    template = active_template(request, body.template_id)
    doc = find_change(body.change_id, body.text, template)
    task_id = orch.start_change_task(doc)
    audit.log_event(active_reviewer(request, template), "change_task_started", task_id,
                    {"change_id": doc.change_id, "pasted": body.text is not None}, template_id=template.id)
    return task_id


def start_request(request: Request, body: RequestTaskBody) -> str:
    template = active_template(request, body.template_id)
    support_request = find_request(body.request_id, template)
    task_id = orch.start_request_task(support_request)
    audit.log_event(active_reviewer(request, template), "request_task_started", task_id,
                    {"request_id": support_request.request_id}, template_id=template.id)
    return task_id


def do_review(request: Request, task_id: str, body: ReviewBody) -> ReviewDecision:
    task = find_task(task_id)
    template = active_template(request, task.template_id)
    reviewer = body.reviewer or active_reviewer(request, template)
    try:
        return review.apply_review(task_id, body.item_id, body.decision, reviewer,
                                   body.edited_content, body.comment)
    except KeyError as error:
        raise HTTPException(404, str(error).strip("'\"")) from None
    except ValueError as error:  # ReviewError and Part 1 validation errors
        raise HTTPException(400, str(error)) from None


def do_retry(task_id: str) -> str:
    task = find_task(task_id)
    if task.status != "failed":
        raise HTTPException(400, f"Only failed tasks can be retried; task {task_id} is {task.status}")
    new_id = orch.retry_task(task_id)
    audit.log_event("Website", "task_retried", new_id, {"retry_of": task_id}, template_id=task.template_id)
    return new_id


def run_search(request: Request, q: str, doc_type: str | None, template_id: str | None) -> list[SearchResult]:
    template = active_template(request, template_id)
    if not q.strip():
        raise HTTPException(400, "The search query must not be empty")
    try:
        return search_module.search(q, k=5, filters={"doc_type": doc_type} if doc_type else None,
                                    template_id=template.id)
    except ValueError as error:
        raise HTTPException(400, str(error)) from None
    except RuntimeError as error:  # empty or outdated index names the rebuild command
        raise HTTPException(503, str(error)) from None


@router.get("/templates", response_model=list[TemplateConfig])
def api_templates():
    return list_templates()


@router.post("/tasks/change")
def api_start_change(request: Request, body: ChangeTaskBody) -> dict:
    return {"task_id": start_change(request, body)}


@router.post("/tasks/request")
def api_start_request(request: Request, body: RequestTaskBody) -> dict:
    return {"task_id": start_request(request, body)}


@router.get("/tasks/{task_id}", response_model=Task)
def api_task(task_id: str):
    return find_task(task_id)


@router.get("/tasks", response_model=list[Task])
def api_tasks(request: Request, template_id: str | None = None,
              status: Literal["running", "pending_review", "approved", "rejected", "failed"] | None = None):
    return orch.list_tasks(template_id=active_template(request, template_id).id, status=status)


@router.post("/tasks/{task_id}/review", response_model=ReviewDecision)
def api_review(request: Request, task_id: str, body: ReviewBody):
    return do_review(request, task_id, body)


@router.post("/tasks/{task_id}/retry")
def api_retry(task_id: str) -> dict:
    return {"task_id": do_retry(task_id)}


@router.get("/search", response_model=list[SearchResult])
def api_search(request: Request, q: str = Query(min_length=1, max_length=500), doc_type: str | None = None,
               template_id: str | None = None):
    return run_search(request, q, doc_type, template_id)


@router.post("/index/rebuild")
def api_rebuild(request: Request, body: RebuildBody | None = None) -> dict:
    template = active_template(request, body.template_id if body else None)
    stats = ingest.ingest_all(template.id)
    audit.log_event(active_reviewer(request, template), "index_rebuilt", None, stats[template.id],
                    template_id=template.id)
    return stats


@router.get("/audit", response_model=list[AuditEvent])
def api_audit(request: Request, task_id: str | None = None, template_id: str | None = None):
    return audit.list_events(task_id=task_id or None, template_id=active_template(request, template_id).id)
