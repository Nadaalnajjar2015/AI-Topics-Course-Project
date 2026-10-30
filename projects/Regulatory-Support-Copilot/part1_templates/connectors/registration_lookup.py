"""Connector for fictional registration records."""
from part1_templates.connectors.base import JsonlRecordConnector
from part1_templates.tools._files import template_dir


class RegistrationLookup(JsonlRecordConnector):
    """Read the immutable university JSONL fixture."""

    def __init__(self, template_id="university"):
        super().__init__(template_dir(template_id) / "records" / "registrations.jsonl", template_id)
