"""Dispatch record searches through the configured connector."""
from contracts.schemas import Record
from part1_templates.connectors import CONNECTORS
from part1_templates.tools.templates import load_template


def search_records(person_id=None, unit_id=None, item=None, status=None, since=None, until=None, template_id=None) -> list[Record]:
    """Search read-only records; filters combine with AND."""
    template = load_template(template_id)
    if template.connector not in CONNECTORS:
        raise ValueError(f"Unknown connector {template.connector!r} for template {template.id}")
    connector = CONNECTORS[template.connector](template_id=template.id)
    return connector.search(person_id=person_id, unit_id=unit_id, item=item, status=status, since=since, until=until)
