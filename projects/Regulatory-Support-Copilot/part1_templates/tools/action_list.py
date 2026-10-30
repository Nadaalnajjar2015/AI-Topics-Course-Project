"""Store approved actions; Part 3 owns their shared ActionItem model."""
from contracts import schemas
from part1_templates.tools._files import read_state, update_state
from part1_templates.tools.changes import get_change
from part1_templates.tools.directory import get_unit, stakeholders_for_unit
from part1_templates.tools.templates import load_template


def _action_model():
    model = getattr(schemas, "ActionItem", None)
    if model is None:
        raise RuntimeError("Part 3 must provide contracts.schemas.ActionItem before action-item integration; see part1_templates/TEAM_ISSUES.md")
    return model


def create_action_item(item, template_id=None) -> str:
    """Save an approved shared ActionItem, rejecting duplicates and foreign IDs."""
    template = load_template(template_id)
    payload = item.model_dump() if hasattr(item, "model_dump") else item
    action = _action_model().model_validate(payload)
    if action.status != "approved":
        raise ValueError("Only human-approved action items may be saved")
    get_change(action.change_id, template.id)
    get_unit(action.unit_id, template.id)
    allowed = {group.stakeholder_id for group in stakeholders_for_unit(action.unit_id, template_id=template.id)}
    if not set(action.stakeholders) <= allowed:
        raise ValueError("Action item contains stakeholders outside its unit and template")
    for field in template.action_item_fields:
        if not hasattr(action, field):
            raise ValueError(f"Action item is missing configured field {field}")

    def append(state):
        items = state.setdefault("action_items", [])
        if any(existing["action_id"] == action.action_id for existing in items):
            raise ValueError(f"Action item {action.action_id} already exists in template {template.id}")
        items.append(action.model_dump(mode="json"))

    update_state(template.id, append)
    return action.action_id


def list_action_items(template_id=None) -> list:
    """Return approved runtime actions; historical examples remain in history/."""
    items = read_state(template_id).get("action_items", [])
    if not items:
        return []
    model = _action_model()
    return [model.model_validate(item) for item in items]
