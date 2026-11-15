"""Append-only audit log and review-decision storage in the tasks SQLite file."""
import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from contracts.schemas import AuditEvent, ReviewDecision
from part5_web.safety.masking import mask

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    template_id TEXT,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    task_id TEXT,
    details TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS review_decisions (
    decision_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    template_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    data TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS audit_events_no_update BEFORE UPDATE ON audit_events
BEGIN SELECT RAISE(ABORT, 'audit events are append-only'); END;
CREATE TRIGGER IF NOT EXISTS audit_events_no_delete BEFORE DELETE ON audit_events
BEGIN SELECT RAISE(ABORT, 'audit events are append-only'); END;
"""


def _db_path() -> Path:
    """Same file as Part 4's tasks, so tests that redirect the task store redirect audit too."""
    try:
        from part4_request_desk.orchestrator import store
        return Path(store.settings.app_db)
    except ImportError:
        from part2_knowledge.common.config import settings
        return Path(settings.app_db)


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30)
    connection.row_factory = sqlite3.Row
    try:
        connection.executescript(_SCHEMA)
        with connection:
            yield connection
    finally:
        connection.close()


def _masked(value: object) -> object:
    if isinstance(value, str):
        return mask(value)
    if isinstance(value, dict):
        return {str(key): _masked(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_masked(item) for item in value]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return mask(str(value))


def log_event(actor: str, action: str, task_id: str | None, details: dict | None = None,
              template_id: str | None = None) -> None:
    """Append one event. Never raises: a broken audit log must not break a workflow."""
    try:
        with _connection() as connection:
            connection.execute(
                "INSERT INTO audit_events (timestamp, template_id, actor, action, task_id, details)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (datetime.now(timezone.utc).isoformat(), template_id, str(actor), str(action), task_id,
                 json.dumps(_masked(details or {}), ensure_ascii=False, default=str)),
            )
    except Exception:  # noqa: BLE001 - the caller must never see audit failures
        logger.exception("Could not write audit event %s for task %s", action, task_id)


def list_events(task_id: str | None = None, template_id: str | None = None,
                limit: int | None = None) -> list[AuditEvent]:
    """Return events newest first, optionally filtered by task and template."""
    filters, values = [], []
    for column, value in (("task_id", task_id), ("template_id", template_id)):
        if value is not None:
            filters.append(f"{column} = ?")
            values.append(value)
    query = "SELECT * FROM audit_events"
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY event_id DESC"
    if limit is not None:
        query += " LIMIT ?"
        values.append(int(limit))
    with _connection() as connection:
        rows = connection.execute(query, values).fetchall()
    return [AuditEvent(event_id=row["event_id"], timestamp=row["timestamp"], template_id=row["template_id"],
                       actor=row["actor"], action=row["action"], task_id=row["task_id"],
                       details=json.loads(row["details"])) for row in rows]


def save_decision(decision: ReviewDecision) -> ReviewDecision:
    """Store a review decision (masked); one decision per task item."""
    safe = ReviewDecision.model_validate(_masked(decision.model_dump(mode="json")))
    with _connection() as connection:
        exists = connection.execute("SELECT 1 FROM review_decisions WHERE task_id = ? AND item_id = ?",
                                    (safe.task_id, safe.item_id)).fetchone()
        if exists:
            raise ValueError(f"Item {safe.item_id} of task {safe.task_id} was already reviewed")
        connection.execute(
            "INSERT INTO review_decisions (decision_id, task_id, template_id, item_id, created_at, data)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (safe.decision_id, safe.task_id, safe.template_id, safe.item_id,
             safe.created_at.isoformat(), safe.model_dump_json()),
        )
    return safe


def list_decisions(task_id: str | None = None) -> list[ReviewDecision]:
    """Return decisions oldest first, for one task or all tasks."""
    query, values = "SELECT data FROM review_decisions", []
    if task_id is not None:
        query += " WHERE task_id = ?"
        values.append(task_id)
    with _connection() as connection:
        rows = connection.execute(query + " ORDER BY created_at, decision_id", values).fetchall()
    return [ReviewDecision.model_validate_json(row["data"]) for row in rows]
