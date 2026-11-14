"""Command-line runner for Part 4 workflows."""

import argparse
import json
from typing import Sequence

from contracts.schemas import Task
from part1_templates.tools.changes import get_change
from part1_templates.tools.requests import get_request
from part2_knowledge.common.config import settings
from part4_request_desk.orchestrator import list_tasks, run_change_sync, run_request_sync


def _print_task(task: Task) -> None:
    print(f"Task {task.task_id}: {task.status} ({task.template_id})")
    for step in task.steps:
        detail = f" — {step.error}" if step.error else ""
        print(f"- {step.name}: {step.status}{detail}")
    print(json.dumps(task.outputs, indent=2, ensure_ascii=False))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Regulatory & Support Copilot tasks.")
    workflow = parser.add_mutually_exclusive_group(required=True)
    workflow.add_argument("--change", help="Change document ID to process.")
    workflow.add_argument("--request", help="Request ID to investigate.")
    workflow.add_argument("--list", action="store_true", help="List stored tasks.")
    parser.add_argument("--template", help="Template ID; defaults to ACTIVE_TEMPLATE.")
    args = parser.parse_args(argv)
    template_id = args.template or settings.active_template

    if args.list:
        tasks = list_tasks(template_id=args.template)
        print(json.dumps([task.model_dump(mode="json") for task in tasks], indent=2))
        return 0

    try:
        if args.change:
            task = run_change_sync(
                get_change(args.change, template_id=template_id)
            )
        else:
            task = run_request_sync(
                get_request(args.request, template_id=template_id)
            )
    except KeyError as error:
        parser.error(str(error))

    _print_task(task)
    return 1 if task.status == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
