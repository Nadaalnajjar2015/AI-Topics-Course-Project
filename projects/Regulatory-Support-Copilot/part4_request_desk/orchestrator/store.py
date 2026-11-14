"""SQLite persistence for orchestrator tasks."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from contracts.schemas import Task
from part2_knowledge.common.config import settings


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    database = Path(settings.app_db)
    database.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database, timeout=30)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    template_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    data TEXT NOT NULL
                )
                """
            )
        yield connection
    finally:
        connection.close()


def save_task(task: Task) -> None:
    """Insert or replace a task, storing the full model as JSON."""
    with _connection() as connection:
        with connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO tasks
                    (task_id, template_id, type, status, created_at, data)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    task.task_id,
                    task.template_id,
                    task.type,
                    task.status,
                    task.created_at.isoformat(),
                    task.model_dump_json(),
                ),
            )


def load_task(task_id: str) -> Task:
    """Load one task or raise KeyError when it does not exist."""
    with _connection() as connection:
        row = connection.execute(
            "SELECT data FROM tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
    if row is None:
        raise KeyError(f"Task {task_id} not found")
    return Task.model_validate_json(row["data"])


def query_tasks(
    template_id: str | None = None,
    type: str | None = None,
    status: str | None = None,
) -> list[Task]:
    """Query tasks by optional fields, newest first."""
    filters: list[str] = []
    values: list[str] = []
    for column, value in (
        ("template_id", template_id),
        ("type", type),
        ("status", status),
    ):
        if value is not None:
            filters.append(f"{column} = ?")
            values.append(value)
    where_clause = f" WHERE {' AND '.join(filters)}" if filters else ""
    query = (
        "SELECT data FROM tasks"
        f"{where_clause} ORDER BY created_at DESC, task_id DESC"
    )
    with _connection() as connection:
        rows = connection.execute(query, values).fetchall()
    return [Task.model_validate_json(row["data"]) for row in rows]
