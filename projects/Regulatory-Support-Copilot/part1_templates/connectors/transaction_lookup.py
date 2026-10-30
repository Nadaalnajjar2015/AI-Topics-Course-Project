"""Connector for fictional transaction records."""
from part1_templates.connectors.base import JsonlRecordConnector
from part1_templates.tools._files import template_dir


class TransactionLookup(JsonlRecordConnector):
    """Read the immutable payments JSONL fixture."""

    def __init__(self, template_id="payments"):
        super().__init__(template_dir(template_id) / "records" / "transactions.jsonl", template_id)
