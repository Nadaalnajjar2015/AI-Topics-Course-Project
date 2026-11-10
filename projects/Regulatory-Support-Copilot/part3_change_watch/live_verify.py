"""Opt-in live template smoke tests and a resumable eight-case evaluation.

Uses only Part 2's public LLM APIs. Reports and full sanitized outputs stay in
ignored runtime storage; no action-item storage or review state is modified.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from importlib.metadata import version
import time

from part1_templates.tools.changes import get_change
from part1_templates.tools.templates import list_templates
from part2_knowledge.common import llm
from part2_knowledge.common.config import PROJECT_ROOT, settings
from part2_knowledge.common.privacy import PrivacyError, mask_text
from part3_change_watch.cli import run
from part3_change_watch.quality_check import aggregate, score_case


@contextmanager
def limited_calls(interval, maximum, rate_retries=2):
    """Space calls; retry only explicit rate limits, with a strict call budget."""
    original = llm.complete_json
    calls = []
    last = None

    def complete(system, user, schema):
        nonlocal last
        for attempt in range(rate_retries + 1):
            if len(calls) >= maximum:
                raise llm.LLMError("Live verification call budget exhausted.")
            delay = max(0, interval - (time.monotonic() - last)) if last is not None else 0
            if delay:
                time.sleep(delay)
            last = time.monotonic()
            entry = {"schema": schema.__name__, "attempt": attempt + 1, "status": "started"}
            calls.append(entry)
            print(json.dumps({"event": "call_started", "number": len(calls), "schema": schema.__name__}), flush=True)
            try:
                result = original(system, user, schema)
                entry["status"] = "success"
                if hasattr(result, "model_dump"):
                    entry["validated_output"] = result.model_dump(mode="json")
                print(json.dumps({"event": "call_succeeded", "number": len(calls), "schema": schema.__name__}), flush=True)
                return result
            except llm.LLMError as exc:
                # The public wrapper supplies safe generic messages, never SDK bodies.
                entry["status"] = "rate_limited" if "rate limit" in str(exc).lower() else "failed"
                if entry["status"] != "rate_limited" or attempt == rate_retries:
                    raise
                print(json.dumps({"event": "rate_limit_backoff", "seconds": 30, "schema": schema.__name__}), flush=True)
                time.sleep(30)
    llm.complete_json = complete
    try:
        yield calls
    finally:
        llm.complete_json = original


def smoke_valid(outputs):
    summary = outputs["summary"]
    return (bool(summary["requirements"]) and bool(outputs["impact_report"]["impacts"])
            and bool(outputs["action_items"])
            and all(a["status"] == "pending_review" for a in outputs["action_items"]))


def _save(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def successful_smokes(root, model):
    """Completed individual cases remain valid when another smoke case failed."""
    passed = {}
    for name in ("smoke.json", "smoke-payments.json", "smoke-university.json"):
        path = root / name
        if not path.exists():
            continue
        prior = json.loads(path.read_text(encoding="utf-8"))
        if prior.get("model") != model or prior.get("provider") != "groq":
            continue
        for row in prior.get("smoke", []):
            if row.get("passed"):
                passed[row["template_id"]] = {"report": name, "case": row,
                                              "prompt_versions": prior.get("prompt_versions", {})}
    return passed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-live", action="store_true", required=True)
    parser.add_argument("--phase", choices=["smoke", "evaluation", "all"], default="all")
    parser.add_argument("--smoke-template", choices=["all", "payments", "university"], default="all")
    parser.add_argument("--model", default="openai/gpt-oss-20b")
    parser.add_argument("--interval", type=float, default=15)
    parser.add_argument("--max-calls", type=int, default=80)
    parser.add_argument("--resume", action="store_true", help="Keep already completed same-model cases after a stopped evaluation.")
    args = parser.parse_args(argv)
    if not 3 <= args.interval <= 30 or not 1 <= args.max_calls <= 100:
        parser.error("interval must be 3..30 seconds and max-calls must be 1..100")
    if not settings.groq_api_key.strip():
        print("LIVE GROQ TEST NOT RUN: local credentials missing.")
        return 2
    # Process-local overrides preserve the user's .env and defaults.
    settings.llm_provider = "groq"
    settings.llm_model = args.model
    root = PROJECT_ROOT / "runtime" / "part3_live"
    suffix = f"-{args.smoke_template}" if args.phase == "smoke" and args.smoke_template != "all" else ""
    report_path = root / f"{args.phase}{suffix}.json"
    report = {"provider": "groq", "model": args.model, "interface_only": False,
              "started_at": datetime.now(timezone.utc).isoformat(), "phase": args.phase,
              "smoke": [], "cases": [], "outputs": {}, "completed": False}
    report["sdk_version"] = version("groq")
    report["prompt_versions"] = {p.stem: p.read_text(encoding="utf-8").splitlines()[0]
                                 for p in (PROJECT_ROOT / "part3_change_watch/prompts").glob("*.md")}
    report["implementation_sha256"] = {
        name: hashlib.sha256((PROJECT_ROOT / name).read_bytes()).hexdigest() for name in (
            "part2_knowledge/common/llm.py", "part3_change_watch/_support.py", "part3_change_watch/watcher.py",
            "part3_change_watch/impact.py", "part3_change_watch/action_planner.py", "part3_change_watch/quality_check.py")
        if (PROJECT_ROOT / name).exists()
    }
    earlier_calls = []
    if args.resume and report_path.exists():
        previous = json.loads(report_path.read_text(encoding="utf-8"))
        if (args.phase != "evaluation" or previous.get("model") != args.model
                or previous.get("prompt_versions") != report["prompt_versions"]
                or previous.get("implementation_sha256") != report["implementation_sha256"]):
            parser.error("Resume requires the same evaluation model, prompt versions and implementation.")
        report = previous
        earlier_calls = report.get("calls", [])
        report.pop("error", None)
    calls = []
    try:
        with limited_calls(args.interval, args.max_calls - len(earlier_calls)) as calls:
            if args.phase in {"smoke", "all"}:
                for template_id, change_id in [("payments", "CHG-P-002"), ("university", "CHG-U-001")]:
                    if args.smoke_template not in {"all", template_id}:
                        continue
                    print(json.dumps({"event": "smoke_started", "template_id": template_id}), flush=True)
                    outputs = run(get_change(change_id, template_id=template_id))
                    report["outputs"][change_id] = outputs
                    passed = smoke_valid(outputs)
                    report["smoke"].append({"template_id": template_id, "change_id": change_id, "passed": passed})
                    _save(report_path, report)
                    print(json.dumps({"event": "smoke_completed", **report["smoke"][-1],
                                      "requirements": len(outputs["summary"]["requirements"]),
                                      "units": sorted({i["unit_id"] for i in outputs["impact_report"]["impacts"]}),
                                      "actions": len(outputs["action_items"])}), flush=True)
                    if not passed:
                        raise ValueError("Template smoke produced no verified pipeline results.")
            if args.phase == "evaluation":
                previous = successful_smokes(root, args.model)
                if set(previous) != {"payments", "university"}:
                    raise ValueError("Both same-model template smoke tests must succeed before evaluation.")
                report["smoke_provenance"] = previous
            if args.phase in {"evaluation", "all"}:
                for template in list_templates():
                    path = settings.templates_dir / template.id / "eval" / "change_eval.json"
                    cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
                    if not cases:
                        raise ValueError("Evaluation cases must not be empty.")
                    for case in cases:
                        if any(row["change_id"] == case["change_id"] for row in report["cases"]):
                            continue
                        print(json.dumps({"event": "case_started", "change_id": case["change_id"]}), flush=True)
                        doc = get_change(case["change_id"], template_id=template.id)
                        outputs = run(doc)
                        row = {"template_id": template.id, **score_case(case, doc, outputs)}
                        report["cases"].append(row)
                        report["outputs"][doc.change_id] = outputs
                        _save(report_path, report)
                        print(json.dumps({"event": "case_completed", **row}), flush=True)
                report["per_template"] = {t: aggregate([r for r in report["cases"] if r["template_id"] == t])
                                          for t in sorted({r["template_id"] for r in report["cases"]})}
                report["overall"] = aggregate(report["cases"])
                report["targets_met"] = report["overall"]["targets_met"] and all(
                    result["targets_met"] for result in report["per_template"].values())
            report["completed"] = True
            return 0 if args.phase == "smoke" or report["targets_met"] else 1
    except (llm.LLMError, PrivacyError) as exc:
        report["error"] = str(exc)
        print(json.dumps({"event": "verification_stopped", "error": report["error"]}), flush=True)
        return 3
    except (ValueError, KeyError, RuntimeError, OSError) as exc:
        report["error"] = "Pipeline/input failure: " + mask_text(str(exc))[:300]
        print(json.dumps({"event": "verification_stopped", "error": report["error"]}), flush=True)
        return 3
    finally:
        report["calls"] = earlier_calls + calls
        report["successful_completions"] = sum(c["status"] == "success" for c in report["calls"])
        report["rate_limited_wrapper_attempts"] = sum(c["status"] == "rate_limited" for c in report["calls"])
        report["sdk_max_retries_per_wrapper_call"] = settings.llm_max_retries
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        _save(report_path, report)
        print(json.dumps({"report": str(report_path), "completed": report["completed"], "wrapper_calls": len(report["calls"])}), flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
