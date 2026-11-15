"""Template and reviewer selection plus shared lookups for pages and the JSON API."""
from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates

from contracts.schemas import ChangeDocument, Request as SupportRequest, TemplateConfig
from part1_templates.tools.changes import get_change, parse_change
from part1_templates.tools.requests import get_request
from part1_templates.tools.templates import list_templates, load_template
from part2_knowledge.common.config import settings
from part4_request_desk import orchestrator as orch
from part5_web.safety.masking import mask

TEMPLATE_COOKIE = "template_id"
REVIEWER_COOKIE = "reviewer"
HTML = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
HTML.env.filters["mask"] = lambda value: mask(value) if isinstance(value, str) else value


def get_template(template_id: str | None) -> TemplateConfig:
    """Load a template or raise 404 with the available IDs."""
    try:
        return load_template(template_id)
    except KeyError as error:
        raise HTTPException(404, str(error).strip("'\"")) from None


def active_template(request: Request, explicit: str | None = None) -> TemplateConfig:
    """Explicit value, then cookie, then ACTIVE_TEMPLATE."""
    chosen = explicit or request.cookies.get(TEMPLATE_COOKIE) or settings.active_template
    if explicit is None and request.cookies.get(TEMPLATE_COOKIE):
        try:
            return load_template(chosen)
        except KeyError:  # stale cookie: fall back quietly
            chosen = settings.active_template
    return get_template(chosen)


def active_reviewer(request: Request, template: TemplateConfig) -> str:
    chosen = request.cookies.get(REVIEWER_COOKIE)
    return chosen if chosen in template.reviewers else template.reviewers[0]


def _owner_of(identifier: str, lookup) -> str | None:
    for other in list_templates():
        try:
            lookup(identifier, template_id=other.id)
            return other.id
        except KeyError:
            continue
    return None


def find_request(request_id: str, template: TemplateConfig) -> SupportRequest:
    """Request in this template; 400 if it belongs to another one, 404 if unknown."""
    try:
        return get_request(request_id, template_id=template.id)
    except KeyError:
        owner = _owner_of(request_id, get_request)
        if owner:
            raise HTTPException(400, f"Request {request_id} belongs to template {owner}, not {template.id}") from None
        raise HTTPException(404, f"Request {request_id} not found in template {template.id}") from None


def find_change(change_id: str | None, text: str | None, template: TemplateConfig) -> ChangeDocument:
    """A stored change by ID, or a pasted document parsed with Part 1's parser."""
    if text is not None:
        if not text.strip():
            raise HTTPException(400, "The pasted change document is empty")
        try:
            return parse_change(text, template_id=template.id)
        except (ValueError, TypeError) as error:
            raise HTTPException(400, f"Could not read the change document: {error}") from None
    if not change_id:
        raise HTTPException(400, "Give a change_id or paste the change text")
    try:
        return get_change(change_id, template_id=template.id)
    except KeyError:
        owner = _owner_of(change_id, get_change)
        if owner:
            raise HTTPException(400, f"Change {change_id} belongs to template {owner}, not {template.id}") from None
        raise HTTPException(404, f"Change {change_id} not found in template {template.id}") from None


def find_task(task_id: str):
    try:
        return orch.get_task(task_id)
    except KeyError:
        raise HTTPException(404, f"Task {task_id} not found") from None


def page(request: Request, name: str, template: TemplateConfig, **values):
    """Render an HTML page with the navigation context every page needs."""
    return HTML.TemplateResponse(request, name, {
        "template": template, "labels": template.labels, "templates": list_templates(),
        "reviewer": active_reviewer(request, template),
        "provider": settings.llm_provider, "model": settings.llm_model,
        "path": request.url.path, "review_count": _review_count(template.id),
        "asset_version": _asset_version(), **values,
    })


STATIC_DIR = Path(__file__).parent / "static"


def _asset_version() -> str:
    """Changes whenever a CSS/JS file changes, so browsers never use a stale cached copy."""
    try:
        return str(max(int(p.stat().st_mtime) for p in STATIC_DIR.glob("*.*")))
    except ValueError:
        return "0"


def _review_count(template_id: str) -> int:
    """Number of tasks waiting for a reviewer (shown next to the menu link)."""
    try:
        return len(orch.list_tasks(template_id=template_id, status="pending_review"))
    except Exception:  # noqa: BLE001 - a menu badge must never break a page
        return 0
