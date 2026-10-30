"""Read units and select stakeholder groups with deterministic scope rules."""
from contracts.schemas import Stakeholder, Unit
from part1_templates.tools._files import read_items, template_dir
from part1_templates.tools.templates import load_template


def list_units(template_id=None) -> list[Unit]:
    """Return the selected organization's units."""
    return [Unit.model_validate(row) for row in read_items(template_dir(template_id) / "units.json", "units")]


def get_unit(unit_id, template_id=None) -> Unit:
    """Find a unit, raising a clear error if its ID is unknown."""
    template_id = load_template(template_id).id
    for unit in list_units(template_id):
        if unit.unit_id == unit_id:
            return unit
    raise KeyError(f"Unit {unit_id} not found in template {template_id}")


def list_stakeholders(template_id=None) -> list[Stakeholder]:
    """Return stakeholder groups with their local configuration."""
    path = template_dir(template_id) / "stakeholders.json"
    return [Stakeholder.model_validate(row) for row in read_items(path, "stakeholders")]


def _matches(group: Stakeholder, scope: str | None) -> bool:
    if scope is None or scope == "all":
        return True
    if "=" in scope:
        key, value = scope.split("=", 1)
        actual = group.attributes.get(key.strip())
        if isinstance(actual, bool):
            return str(actual).lower() == value.strip().lower()
        return actual is not None and str(actual) == value.strip()
    return group.type == scope or group.attributes.get(scope) is True


def stakeholders_for_unit(unit_id, scope=None, template_id=None) -> list[Stakeholder]:
    """Match unit membership, then all/type/true-attribute/key=value scope."""
    template_id = load_template(template_id).id
    get_unit(unit_id, template_id)
    return [group for group in list_stakeholders(template_id)
            if unit_id in group.units and _matches(group, scope)]
