"""Run every eval case of each template through the system and report accuracy.

    python -m part5_web.evaluation.run_eval --template payments|university|all
                                            [--only changes|requests|search] [--limit N] [--pause S]

Writes runtime/eval/report.json and docs/evaluation-report.md. Tasks run in a separate
database (runtime/eval/eval.db) so evaluation runs do not fill the website dashboard.
"""
import argparse
import json
import re
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from part1_templates.tools.changes import get_change
from part1_templates.tools.requests import get_request
from part1_templates.tools.templates import list_templates, load_template
from part2_knowledge.common.config import PROJECT_ROOT, settings
from part2_knowledge.knowledge_base import search as search_module
from part4_request_desk import orchestrator as orch
from part4_request_desk.orchestrator import store
from part5_web.evaluation.report import write_markdown
from part5_web.safety.masking import find_leaks

EVAL_DIR = PROJECT_ROOT / "runtime" / "eval"
REPORT_JSON = EVAL_DIR / "report.json"
REPORT_MD = PROJECT_ROOT / "docs" / "evaluation-report.md"
AREAS = ("changes", "requests", "search")


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip().casefold()


def _cases(template_id: str, name: str, limit: int | None) -> list[dict]:
    path = settings.templates_dir / template_id / "eval" / f"{name}_eval.json"
    cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
    return cases[:limit] if limit else cases


def _seconds(task) -> float:
    times = [(s.finished_at - s.started_at).total_seconds() for s in task.steps if s.started_at and s.finished_at]
    return round(sum(times), 3)


def _failed_error(task) -> str:
    return next((s.error or "failed" for s in task.steps if s.status == "failed"), "")


_PROVIDER_LIMIT = ("rate limit", "timeout", "provider failure")


def _run(job, pause: float = 0.0, retries: int = 3):
    """Run one task; if it failed only because the provider was busy, wait and run it again.

    Free model plans limit requests per minute. Those failures say nothing about the
    agents, so they are retried (30 s, 60 s, 90 s) instead of being scored as wrong.
    """
    for attempt in range(retries + 1):
        if pause:
            time.sleep(pause)
        task = job()
        error = _failed_error(task).casefold()
        if task.status != "failed" or not any(word in error for word in _PROVIDER_LIMIT) or attempt == retries:
            return task
        time.sleep(30 * (attempt + 1))
    return task


def score_change(case: dict, task, doc_text: str) -> dict:
    """Compare one Change Watch task with its answer-set case."""
    row = {"id": case["change_id"], "status": task.status, "seconds": _seconds(task), "error": _failed_error(task)}
    out = task.outputs
    summary, report = out.get("summary") or {}, out.get("impact_report") or {}
    requirements = summary.get("requirements", [])
    units = {i["unit_id"] for i in report.get("impacts", [])}
    groups = {s for i in report.get("impacts", []) for s in i["stakeholders"]}
    expected_units, expected_groups = set(case["expected_units"]), set(case["expected_stakeholders"])
    text = _norm(json.dumps(out, ensure_ascii=False))
    row.update({
        "requirements_found": len(requirements),
        "requirement_recall": len(requirements) >= case["expected_requirements_min"],
        "unit_precision": len(units & expected_units) / len(units) if units else float(not expected_units),
        "unit_recall": len(units & expected_units) / len(expected_units) if expected_units else 1.0,
        "stakeholder_accuracy": groups == expected_groups,
        "quote_validity": (sum(_norm(r["source_quote"]) in _norm(doc_text) for r in requirements) / len(requirements)
                           if requirements else 0.0),
        "key_fact_coverage": (sum(_norm(f) in text for f in case["key_facts"]) / len(case["key_facts"])
                              if case["key_facts"] else 1.0),
        "actual_units": sorted(units), "expected_units": sorted(expected_units),
    })
    return row


def score_request(case: dict, task) -> dict:
    """Compare one Request Desk task with its answer-set case."""
    inv = task.outputs.get("investigation") or {}
    root = _norm(inv.get("root_cause", ""))
    return {
        "id": case["request_id"], "status": task.status, "seconds": _seconds(task), "error": _failed_error(task),
        "item_accuracy": inv.get("item") == case["expected_item"],
        "reason_code_accuracy": inv.get("reason_code") == case["expected_reason_code"],
        "escalation_accuracy": inv.get("escalate") == case["expected_escalate"],
        "root_cause_keywords": bool(inv) and all(_norm(k) in root for k in case["root_cause_keywords"]),
        "actual": {k: inv.get(k) for k in ("item", "reason_code", "escalate")},
        "expected": {"item": case["expected_item"], "reason_code": case["expected_reason_code"],
                     "escalate": case["expected_escalate"]},
    }


def score_search(case: dict, template_id: str) -> dict:
    try:
        sources = [r.source for r in search_module.search(case["query"], k=5, template_id=template_id)]
        error = ""
    except Exception as exc:  # noqa: BLE001 - an unbuilt index is a reported failure
        sources, error = [], str(exc)
    return {"id": case["query"], "hit": case["expected_source"] in sources, "expected": case["expected_source"],
            "returned": sources, "error": error}


def _mean(rows: list[dict], key: str) -> float | None:
    return round(sum(float(r[key]) for r in rows) / len(rows), 3) if rows else None


class _PromptRecorder:
    """Counts unmasked values in every prompt the LLM wrapper would send."""

    def __init__(self):
        self.leaks: dict[str, int] = {}

    @contextmanager
    def watch(self):
        from part2_knowledge.common import llm
        original = getattr(llm, "_masked_prompts", None)
        if original is None:
            yield
            return

        def recorded(system, user):
            masked = original(system, user)
            for text in masked:
                for kind, count in find_leaks(text).items():
                    self.leaks[kind] = self.leaks.get(kind, 0) + count
            return masked
        llm._masked_prompts = recorded
        try:
            yield
        finally:
            llm._masked_prompts = original


@contextmanager
def _eval_database():
    original = store.settings
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    store.settings = original.model_copy(update={"app_db": EVAL_DIR / "eval.db"})
    try:
        yield
    finally:
        store.settings = original


def evaluate_template(template_id: str, only: str | None = None, limit: int | None = None,
                      pause: float = 0.0) -> dict:
    template = load_template(template_id)
    recorder = _PromptRecorder()
    result = {"organization": template.organization, "cases": {}, "metrics": {}}
    with _eval_database(), recorder.watch():
        if only in (None, "search"):
            result["cases"]["search"] = [score_search(c, template.id) for c in _cases(template.id, "search", limit)]
        if only in (None, "changes"):
            rows = []
            for case in _cases(template.id, "change", limit):
                doc = get_change(case["change_id"], template_id=template.id)
                rows.append(score_change(case, _run(lambda: orch.run_change_sync(doc), pause), doc.text))
            result["cases"]["changes"] = rows
        if only in (None, "requests"):
            rows = []
            for case in _cases(template.id, "request", limit):
                request = get_request(case["request_id"], template_id=template.id)
                task = _run(lambda: orch.run_request_sync(request), pause)
                row = score_request(case, task)
                reply_leaks = find_leaks((task.outputs.get("investigation") or {}).get("draft_reply", ""))
                for kind, count in reply_leaks.items():
                    recorder.leaks[kind] = recorder.leaks.get(kind, 0) + count
                rows.append(row)
            result["cases"]["requests"] = rows
    cases, metrics = result["cases"], result["metrics"]
    if "search" in cases:
        metrics["Search"] = {"hit@5": _mean(cases["search"], "hit"), "cases": len(cases["search"])}
    if "changes" in cases:
        rows = cases["changes"]
        metrics["Change Watch"] = {name: _mean(rows, key) for name, key in (
            ("requirement recall", "requirement_recall"), ("unit precision", "unit_precision"),
            ("unit recall", "unit_recall"), ("stakeholder accuracy", "stakeholder_accuracy"),
            ("quote validity", "quote_validity"), ("key-fact coverage", "key_fact_coverage"))}
        metrics["Change Watch"]["cases"] = len(rows)
    if "requests" in cases:
        rows = cases["requests"]
        metrics["Request Desk"] = {name: _mean(rows, key) for name, key in (
            ("item accuracy", "item_accuracy"), ("reason-code accuracy", "reason_code_accuracy"),
            ("escalation accuracy", "escalation_accuracy"), ("root-cause keywords", "root_cause_keywords"))}
        metrics["Request Desk"]["cases"] = len(rows)
    timed = cases.get("changes", []) + cases.get("requests", [])
    metrics["Safety"] = {"masking leaks": sum(recorder.leaks.values()), **{f"leaks: {k}": v for k, v in recorder.leaks.items()}}
    metrics["Speed"] = {"average seconds per task": _mean(timed, "seconds"), "failed tasks":
                        sum(r["status"] == "failed" for r in timed)}
    result["display"] = {area: {name: _display(name, value) for name, value in values.items()}
                         for area, values in metrics.items()}
    return result


def _display(name: str, value) -> str:
    if value is None:
        return "–"
    if name in {"cases", "masking leaks", "failed tasks"} or name.startswith("leaks:"):
        return str(value)
    if "seconds" in name:
        return f"{value:.2f} s"
    return f"{value * 100:.0f}%"


def _worst(templates: dict) -> list[dict]:
    failures = []
    for tid, data in templates.items():
        for row in data["cases"].get("search", []):
            if not row["hit"]:
                failures.append((1.0, tid, "Search", row["id"], row["error"] or f"expected {row['expected']}"))
        for row in data["cases"].get("changes", []):
            score = (row["unit_recall"] + row["key_fact_coverage"] + row["stakeholder_accuracy"]) / 3
            if row["status"] == "failed" or score < 1:
                problem = row["error"] or f"units {row['actual_units']} vs {row['expected_units']}, found {row['requirements_found']} requirements"
                failures.append((score, tid, "Change Watch", row["id"], problem))
        for row in data["cases"].get("requests", []):
            keys = ("item_accuracy", "reason_code_accuracy", "escalation_accuracy", "root_cause_keywords")
            score = sum(row[k] for k in keys) / len(keys)
            if score < 1:
                failures.append((score, tid, "Request Desk", row["id"], row["error"] or f"got {row['actual']}, expected {row['expected']}"))
    failures.sort(key=lambda f: f[0])
    return [{"template_id": t, "area": a, "id": i, "problem": p[:300]} for _, t, a, i, p in failures[:5]]


def run(template: str = "all", only: str | None = None, limit: int | None = None,
        write: bool = True, pause: float = 0.0) -> dict:
    ids = [t.id for t in list_templates()] if template == "all" else [load_template(template).id]
    templates = {tid: evaluate_template(tid, only, limit, pause) for tid in ids}
    metric_rows: dict[str, list[str]] = {}
    for data in templates.values():
        for area, values in data["metrics"].items():
            metric_rows.setdefault(area, [])
            metric_rows[area] += [m for m in values if m not in metric_rows[area]]
    report = {"generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
              "provider": settings.llm_provider, "model": settings.llm_model,
              "templates": templates, "metric_rows": metric_rows, "worst_failures": _worst(templates)}
    if write:
        EVAL_DIR.mkdir(parents=True, exist_ok=True)
        REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        REPORT_MD.write_text(write_markdown(report), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate the agents for each template.")
    parser.add_argument("--template", default="all", help="payments, university or all")
    parser.add_argument("--only", choices=AREAS, help="run one area only")
    parser.add_argument("--limit", type=int, help="first N cases of each file")
    parser.add_argument("--pause", type=float, default=0.0,
                        help="seconds to wait before each task (free model plans limit requests per minute)")
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")
    if not 0 <= args.pause <= 300:
        parser.error("--pause must be between 0 and 300")
    try:
        report = run(args.template, args.only, args.limit, pause=args.pause)
    except KeyError as error:
        parser.error(str(error))
    for tid, data in report["templates"].items():
        print(f"== {data['organization']} ({tid})")
        for area, values in data["display"].items():
            print(f"  {area}: " + ", ".join(f"{k} {v}" for k, v in values.items()))
    print(f"Wrote {REPORT_JSON} and {REPORT_MD}")
    if settings.llm_provider == "fake":
        print("NOTE: fake provider – this checks the script only; it is not an accuracy result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
