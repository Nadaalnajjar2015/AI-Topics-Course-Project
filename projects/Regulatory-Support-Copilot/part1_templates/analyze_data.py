"""Read complete fixture files and print coverage metrics (no connector row cap).

Run from the project root: python -m part1_templates.analyze_data
The report describes synthetic demonstration coverage, not population statistics.
"""
from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent / "templates"


def analyze(template_dir: Path) -> dict:
    """Measure data breadth and expose gaps without modifying any fixture."""
    def read(relative, key):
        return json.loads((template_dir / relative).read_text(encoding="utf-8"))[key]

    records = [row for path in sorted((template_dir / "records").glob("*.jsonl"))
               for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
               if "_note" not in (row := json.loads(line))]
    requests = read("requests/requests.json", "requests")
    cases = read("eval/request_eval.json", "cases")
    history = read("history/past_requests.json", "requests")
    units = read("units.json", "units")
    request_by_id = {row["request_id"]: row for row in requests}
    unit_metrics = {}
    for unit in units:
        identifier = unit["unit_id"]
        rows = [row for row in records if row["unit_id"] == identifier]
        matched_cases = [case for case in cases if case["request_id"] in request_by_id
                         and any(row["person_id"] == request_by_id[case["request_id"]]["person_id"]
                                 and row["item"] == case["expected_item"] for row in rows)]
        reasons = sorted({row["reason_code"] for row in rows if row["reason_code"]})
        evaluated = {case["expected_reason_code"] for case in matched_cases}
        unit_metrics[identifier] = {
            "records": len(rows), "people": len({row["person_id"] for row in rows}),
            "unique_items": len({row["item"] for row in rows}),
            "statuses": dict(sorted(Counter(row["status"] for row in rows).items())),
            "failure_reasons": reasons, "record_backed_request_cases": len(matched_cases),
            "unevaluated_failure_reasons": sorted(set(reasons) - evaluated),
        }

    normalize = lambda text: re.sub(r"\W+", " ", text.lower()).strip()
    active_questions = {normalize(row["body"]) for row in requests}
    historical_questions = {normalize(row["question"]) for row in history}
    known_reasons = {row["reason_code"] for row in records if row["reason_code"]}
    evaluated_reasons = {case["expected_reason_code"] for case in cases}
    return {
        "template_id": template_dir.name,
        "records": len(records), "people": len({row["person_id"] for row in records}),
        "documents": len(list((template_dir / "documents").glob("*.md"))),
        "changes": len(list((template_dir / "changes").glob("*.md"))),
        "requests": len(requests), "historical_requests": len(history),
        "eval_cases": {name: len(read(f"eval/{name}_eval.json", "cases")) for name in ("change", "request", "search")},
        "date_range": [min(row["timestamp"] for row in records), max(row["timestamp"] for row in records)],
        "statuses": dict(sorted(Counter(row["status"] for row in records).items())),
        "reason_codes": dict(sorted(Counter(row["reason_code"] or "SUCCESS" for row in records).items())),
        "exact_duplicate_records": len(records) - len({json.dumps(row, sort_keys=True) for row in records}),
        "repeated_person_item_events": len(records) - len({(row["person_id"], row["item"]) for row in records}),
        "history_question_overlap": sorted(active_questions & historical_questions),
        "missing_request_evaluations": sorted(set(request_by_id) - {case["request_id"] for case in cases}),
        "orphan_request_evaluations": sorted({case["request_id"] for case in cases} - set(request_by_id)),
        "unevaluated_failure_reasons": sorted(known_reasons - evaluated_reasons),
        "missing_study_plans": [unit["unit_id"] for unit in units if unit["type"] == "program"
                                and not (template_dir / "documents" / f"study_plan_{unit['unit_id']}.md").is_file()],
        "units": unit_metrics,
    }


if __name__ == "__main__":
    print(json.dumps([analyze(path) for path in sorted(ROOT.iterdir()) if (path / "template.yaml").is_file()], indent=2))
