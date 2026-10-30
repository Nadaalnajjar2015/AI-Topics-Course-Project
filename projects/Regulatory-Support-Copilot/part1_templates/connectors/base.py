"""Read-only record connector contract and common JSONL filtering."""
from abc import ABC, abstractmethod
from datetime import date, datetime, time, timezone
import json
from pathlib import Path

from contracts.schemas import Record


def _time_bound(value, *, end=False):
    if value is None:
        return None
    if isinstance(value, str):
        value = datetime.fromisoformat(value) if "T" in value or " " in value else date.fromisoformat(value)
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, date):
        result = datetime.combine(value, time.max if end else time.min)
    else:
        raise TypeError("Time filters must be an ISO date, datetime, or ISO string")
    # Fixtures without an offset are treated as UTC; aware filters are normalized.
    return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result.astimezone(timezone.utc)


class RecordConnector(ABC):
    """Connector implementations supply all optional, combinable search filters."""

    @abstractmethod
    def search(self, person_id=None, unit_id=None, item=None, status=None, since=None, until=None) -> list[Record]:
        """Return at most 200 matches, newest first, without changing the source."""
        raise NotImplementedError


class JsonlRecordConnector(RecordConnector):
    """Shared mechanics; concrete connectors choose the source and template."""

    def __init__(self, path: Path, template_id: str):
        self.path = Path(path)
        self.template_id = template_id

    def search(self, person_id=None, unit_id=None, item=None, status=None, since=None, until=None) -> list[Record]:
        """Validate the JSONL and combine exact filters with inclusive time bounds."""
        lower, upper = _time_bound(since), _time_bound(until, end=True)
        if lower is not None and upper is not None and lower > upper:
            raise ValueError("since must not be after until")
        matches = []
        with self.path.open(encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                row = json.loads(line)
                if set(row) == {"_note"}:
                    continue
                record = Record.model_validate(row)
                if record.template_id != self.template_id:
                    raise ValueError(f"Record {record.record_id} belongs to a different template")
                filters = {"person_id": person_id, "unit_id": unit_id, "item": item, "status": status}
                if any(value is not None and getattr(record, key) != value for key, value in filters.items()):
                    continue
                timestamp = _time_bound(record.timestamp)
                if lower is not None and timestamp < lower or upper is not None and timestamp > upper:
                    continue
                matches.append(record)
        return sorted(matches, key=lambda row: (_time_bound(row.timestamp), row.record_id), reverse=True)[:200]
