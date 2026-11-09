"""Sequential eight-case quality runner. Fake results never establish accuracy."""
import argparse
import json
import sys
import time

from part1_templates.tools.changes import get_change
from part1_templates.tools.templates import list_templates
from part2_knowledge.common.config import settings
from part2_knowledge.common.llm import LLMError
from part2_knowledge.common.privacy import PrivacyError
from part3_change_watch.cli import run
from part3_change_watch.watcher import normalize


def score_case(case, doc, outputs):
    summary, report = outputs["summary"], outputs["impact_report"]
    requirements = summary["requirements"]
    actual_units = {i["unit_id"] for i in report["impacts"]}
    expected_units = set(case["expected_units"])
    actual_groups = {s for i in report["impacts"] for s in i["stakeholders"]}
    expected_groups = set(case["expected_stakeholders"])
    matched = actual_units & expected_units
    # Score generated narratives and deterministic effective date, excluding copied
    # retrieval/source quotes so retrieval alone cannot satisfy fact coverage.
    facts_text = json.dumps({"summary": summary["summary_text"], "effective_date": summary["effective_date"],
                            "requirements": [r["description"] for r in requirements],
                            "reasons": [i["reason"] for i in report["impacts"]],
                            "actions": [{"title": a["title"], "description": a["description"],
                                         "checks": a["checks"]} for a in outputs["action_items"]]}, ensure_ascii=False).casefold()
    facts = case["key_facts"]
    return {
        "change_id": doc.change_id, "requirements_found": len(requirements),
        "requirements_minimum": case["expected_requirements_min"],
        "requirement_recall_minimum": min(1.0, len(requirements) / case["expected_requirements_min"])
        if case["expected_requirements_min"] else 1.0,
        "minimum_met": len(requirements) >= case["expected_requirements_min"],
        "unit_precision": len(matched) / len(actual_units) if actual_units else float(not expected_units),
        "unit_recall": len(matched) / len(expected_units) if expected_units else 1.0,
        "actual_units": sorted(actual_units), "expected_units": sorted(expected_units),
        "stakeholder_exact": actual_groups == expected_groups,
        "actual_stakeholders": sorted(actual_groups), "expected_stakeholders": sorted(expected_groups),
        "quote_validity": sum(bool(normalize(r["source_quote"])) and normalize(r["source_quote"]) in normalize(doc.text)
                              for r in requirements) / len(requirements) if requirements else 0.0,
        "key_fact_coverage": sum(fact.casefold() in facts_text for fact in facts) / len(facts) if facts else 1.0,
    }


def aggregate(rows):
    if not rows:
        raise ValueError("Evaluation cases must not be empty.")
    result = {name: sum(row[name] for row in rows) / len(rows) for name in
              ("requirement_recall_minimum", "unit_precision", "unit_recall", "stakeholder_exact", "quote_validity", "key_fact_coverage")}
    result["all_minimums_met"] = all(row["minimum_met"] for row in rows)
    result["targets_met"] = (result["all_minimums_met"] and result["unit_precision"] >= .8
                             and result["unit_recall"] >= .8 and result["stakeholder_exact"] == 1
                             and result["quote_validity"] == 1 and result["key_fact_coverage"] >= .8)
    return result


def evaluate(template_id=None):
    rows = []
    for template in list_templates(template_id):
        path = settings.templates_dir / template.id / "eval" / "change_eval.json"
        cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
        if not cases:
            raise ValueError("Evaluation cases must not be empty.")
        for case in cases:
            doc = get_change(case["change_id"], template_id=template.id)
            # Rate limiting is applied per complete_json call by main(), not per case.
            row = score_case(case, doc, run(doc))
            rows.append({"template_id": template.id, **row})
    per_template = {t: aggregate([r for r in rows if r["template_id"] == t])
                    for t in sorted({r["template_id"] for r in rows})}
    overall = aggregate(rows)
    return {"provider": settings.llm_provider, "model": settings.llm_model,
            "interface_only": settings.llm_provider == "fake", "cases": rows,
            "per_template": per_template, "overall": overall,
            "targets_met": overall["targets_met"] and all(t["targets_met"] for t in per_template.values())}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", default="all")
    parser.add_argument("--allow-live", action="store_true", help="Explicitly permit paid/network Groq calls.")
    parser.add_argument("--interval", type=float, default=3, help="Seconds between live calls (minimum 3, maximum 60).")
    args = parser.parse_args(argv)
    if not 3 <= args.interval <= 60:
        parser.error("--interval must be between 3 and 60 seconds")
    if settings.llm_provider != "fake" and (settings.llm_provider != "groq" or not args.allow_live
                                             or not settings.groq_api_key.strip()):
        print("LIVE GROQ QUALITY EVALUATION NOT RUN: requires groq provider, local key and --allow-live.", file=sys.stderr)
        return 2
    from part2_knowledge.common import llm
    original = llm.complete_json
    smoke_result = None
    try:
        if settings.llm_provider == "groq":
            from part3_change_watch.live_smoke import smoke
            def bounded(*args, **kwargs):
                time.sleep(args_interval)
                return original(*args, **kwargs)
            args_interval = args.interval
            llm.complete_json = bounded
            smoke_result = smoke()
        result = evaluate(None if args.template == "all" else args.template)
        result["smoke_test"] = smoke_result
        print(json.dumps(result, indent=2))
        if result["interface_only"]:
            print("FAKE: interface check only. LIVE GROQ QUALITY EVALUATION NOT RUN.", file=sys.stderr)
            return 0
        return 0 if result["targets_met"] else 1
    except (KeyError, ValueError, LLMError, PrivacyError, RuntimeError):
        print("Evaluation stopped: check input, provider configuration and KB ingestion; no accuracy claim.", file=sys.stderr)
        return 3
    finally:
        llm.complete_json = original


if __name__ == "__main__":
    raise SystemExit(main())
