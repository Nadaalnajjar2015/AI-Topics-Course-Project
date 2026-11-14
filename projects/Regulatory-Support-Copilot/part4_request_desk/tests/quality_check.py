"""Evaluate real Request Investigator runs against the template request sets."""
import argparse
from contextlib import contextmanager
from dataclasses import dataclass
import json
from pathlib import Path
import re
import tempfile
import time
from typing import Iterator, Sequence

from contracts.schemas import Investigation
from part1_templates.tools.requests import list_requests
from part2_knowledge.common.config import settings
from part4_request_desk.orchestrator import run_request_sync, store

_PRIVATE_PATTERNS = (
    re.compile(r"[\w.+*-]+@[\w.-]+\.[^\W\d_]{2,63}\b", re.UNICODE),
    re.compile(r"\b[A-Z]{2}\d{2}(?:[ \t]*[A-Z0-9]){11,30}\b", re.IGNORECASE),
    re.compile(r"(?<!\w)(?:\+|00)\d{1,3}(?:[ \t().-]*[\dXx]){7,14}(?!\w)"),
    re.compile(r"(?<!\d)\d(?:[ \t().-]*\d){9,}(?!\d)"),
    re.compile(r"(?i)\b(?:national\s*(?:id|identifier)|account(?:\s*(?:number|no\.?))?|"
               r"phone|mobile|telephone)\s*[:=#]?\s*\d[\dXx \t().+-]{6,}\b"),
)


@dataclass(frozen=True)
class CaseResult:
    request_id: str
    expected_item: str | None
    actual_item: str | None
    item_correct: bool
    expected_reason_code: str | None
    actual_reason_code: str | None
    reason_code_correct: bool
    expected_escalate: bool
    actual_escalate: bool
    escalation_correct: bool
    keyword_matches: int
    keyword_count: int
    privacy_clean: bool
    elapsed_seconds: float


@contextmanager
def _temporary_task_database() -> Iterator[None]:
    original_settings = store.settings
    with tempfile.TemporaryDirectory(prefix="part4-quality-") as directory:
        store.settings = original_settings.model_copy(
            update={"app_db": Path(directory) / "tasks.db"}
        )
        try:
            yield
        finally:
            store.settings = original_settings


def _has_unmasked_private_data(text: str) -> bool:
    return any(pattern.search(text) for pattern in _PRIVATE_PATTERNS)


def _evaluate_case(case: dict[str, object], investigation: Investigation, elapsed: float) -> CaseResult:
    expected_item = case["expected_item"]
    expected_reason_code = case["expected_reason_code"]
    expected_escalate = case["expected_escalate"]
    keywords = case["root_cause_keywords"]
    if not isinstance(keywords, list) or not all(isinstance(word, str) for word in keywords):
        raise ValueError(f"{case.get('request_id')}: root_cause_keywords must be a string list.")
    root_cause = investigation.root_cause.casefold()
    keyword_matches = sum(keyword.casefold() in root_cause for keyword in keywords)
    return CaseResult(
        request_id=str(case["request_id"]),
        expected_item=expected_item if isinstance(expected_item, str) else None,
        actual_item=investigation.item,
        item_correct=investigation.item == expected_item,
        expected_reason_code=(
            expected_reason_code if isinstance(expected_reason_code, str) else None
        ),
        actual_reason_code=investigation.reason_code,
        reason_code_correct=investigation.reason_code == expected_reason_code,
        expected_escalate=bool(expected_escalate),
        actual_escalate=investigation.escalate,
        escalation_correct=investigation.escalate == expected_escalate,
        keyword_matches=keyword_matches,
        keyword_count=len(keywords),
        privacy_clean=not _has_unmasked_private_data(investigation.draft_reply),
        elapsed_seconds=elapsed,
    )


def run_template(template_id: str) -> list[CaseResult]:
    """Run and score every evaluation request for one template."""
    eval_path = Path(settings.templates_dir) / template_id / "eval" / "request_eval.json"
    payload = json.loads(eval_path.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"{eval_path} must contain a nonempty 'cases' array.")
    requests = {request.request_id: request for request in list_requests(template_id=template_id)}
    results: list[CaseResult] = []
    with _temporary_task_database():
        for case in cases:
            if not isinstance(case, dict) or not isinstance(case.get("request_id"), str):
                raise ValueError(f"{eval_path} contains a malformed evaluation case.")
            request_id = case["request_id"]
            if request_id not in requests:
                raise KeyError(f"Evaluation request {request_id} is missing from template {template_id}.")
            started = time.perf_counter()
            task = run_request_sync(requests[request_id])
            elapsed = time.perf_counter() - started
            if task.status != "pending_review":
                errors = [step.error for step in task.steps if step.status == "failed"]
                raise RuntimeError(
                    f"{request_id} task failed: {'; '.join(error for error in errors if error)}"
                )
            raw_investigation = task.outputs.get("investigation")
            if not isinstance(raw_investigation, dict):
                raise ValueError(f"{request_id} task has no JSON investigation output.")
            investigation = Investigation.model_validate(raw_investigation)
            results.append(_evaluate_case(case, investigation, elapsed))
    return results


def _print_table(template_id: str, results: list[CaseResult]) -> None:
    columns = ("Request", "Item actual/expected", "Code actual/expected", "Escalate actual/expected",
               "Keywords", "Privacy", "Seconds")
    rows = [
        (
            row.request_id,
            f"{row.actual_item or '-'} / {row.expected_item or '-'}",
            f"{row.actual_reason_code or '-'} / {row.expected_reason_code or '-'}",
            f"{row.actual_escalate} / {row.expected_escalate}",
            f"{row.keyword_matches}/{row.keyword_count}",
            "PASS" if row.privacy_clean else "FAIL",
            f"{row.elapsed_seconds:.2f}",
        )
        for row in results
    ]
    widths = [
        max(len(columns[index]), *(len(row[index]) for row in rows))
        for index in range(len(columns))
    ]
    print(f"\n{template_id} request quality")
    print(" | ".join(value.ljust(widths[index]) for index, value in enumerate(columns)))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(" | ".join(value.ljust(widths[index]) for index, value in enumerate(row)))
    total_keywords = sum(row.keyword_count for row in results)
    matched_keywords = sum(row.keyword_matches for row in results)
    count = len(results)
    print(
        f"Totals: item {sum(row.item_correct for row in results)}/{count}; "
        f"reason code {sum(row.reason_code_correct for row in results)}/{count}; "
        f"escalation {sum(row.escalation_correct for row in results)}/{count}; "
        f"root-cause keywords {matched_keywords}/{total_keywords}; "
        f"privacy {sum(row.privacy_clean for row in results)}/{count}; "
        f"average {sum(row.elapsed_seconds for row in results) / count:.2f}s/request"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate Request Investigator against template fixtures.")
    parser.add_argument("--template", choices=("payments", "university", "all"), default="all")
    args = parser.parse_args(argv)
    if settings.llm_provider == "fake":
        parser.error(
            "Quality evaluation requires the team's configured real LLM provider; "
            "the fake provider is for tests and is not an accuracy measurement."
        )
    template_ids = ("payments", "university") if args.template == "all" else (args.template,)
    for template_id in template_ids:
        _print_table(template_id, run_template(template_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
