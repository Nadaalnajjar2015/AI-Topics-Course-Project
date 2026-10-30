"""Read immutable request fixtures and overlay approved status changes."""
from contracts.schemas import Request
from part1_templates.tools._files import read_items, read_state, template_dir, update_state
from part1_templates.tools.templates import load_template


def list_requests(template_id=None) -> list[Request]:
    """Return requests with runtime status overrides."""
    template_id = load_template(template_id).id
    path = template_dir(template_id) / "requests" / "requests.json"
    overrides = read_state(template_id).get("request_statuses", {})
    requests = []
    for row in read_items(path, "requests"):
        if row["template_id"] != template_id:
            raise ValueError(f"Request {row['request_id']} belongs to a different template")
        row = {**row, "status": overrides.get(row["request_id"], row["status"])}
        requests.append(Request.model_validate(row))
    return requests


def get_request(request_id, template_id=None) -> Request:
    """Find a request by ID within the selected template."""
    template_id = load_template(template_id).id
    for request in list_requests(template_id):
        if request.request_id == request_id:
            return request
    raise KeyError(f"Request {request_id} not found in template {template_id}")


def set_request_status(request_id, status, template_id=None) -> Request:
    """Persist a status after the caller has obtained human approval."""
    template_id = load_template(template_id).id
    request = get_request(request_id, template_id)
    updated = Request.model_validate({**request.model_dump(), "status": status})
    update_state(template_id, lambda state: state.setdefault("request_statuses", {}).__setitem__(request_id, status))
    return updated
