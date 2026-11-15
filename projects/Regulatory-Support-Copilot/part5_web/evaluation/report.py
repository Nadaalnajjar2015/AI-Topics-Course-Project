"""Turn an evaluation report dict into docs/evaluation-report.md."""


def _table(report: dict, area: str) -> list[str]:
    ids = list(report["templates"])
    names = [report["templates"][t]["organization"] for t in ids]
    lines = [f"| Metric | {' | '.join(names)} |", "| --- |" + " --- |" * len(ids)]
    for metric in report["metric_rows"][area]:
        cells = [report["templates"][t]["display"].get(area, {}).get(metric, "–") for t in ids]
        lines.append(f"| {metric} | {' | '.join(cells)} |")
    return lines


def write_markdown(report: dict) -> str:
    fake = report["provider"] == "fake"
    lines = [
        "# Evaluation report",
        "",
        f"- **Date:** {report['generated_at']}",
        f"- **Provider / model:** {report['provider']} / `{report['model']}`",
        "- **Data:** Part 1 answer sets (`part1_templates/templates/<id>/eval/*.json`), mock data only.",
        "- **Command:** `python -m part5_web.evaluation.run_eval --template all`",
        "",
    ]
    if fake:
        lines += ["> **Fake provider run.** This checks that the evaluation script and every workflow run end to end.",
                  "> The fake model returns fixed answers, so Change Watch and root-cause numbers are **not** accuracy",
                  "> results. Re-run with the demo model (for example `LLM_PROVIDER=groq`) for the real result.", ""]
    for area in report["metric_rows"]:
        lines += [f"## {area}", "", *_table(report, area), ""]
    lines += ["## Five worst failures", ""]
    if report["worst_failures"]:
        lines += [f"{n}. `{f['template_id']}` · {f['area']} · `{f['id']}` – {f['problem']}"
                  for n, f in enumerate(report["worst_failures"], 1)]
    else:
        lines.append("None – every case passed.")
    lines += [
        "",
        "## Discussion",
        "",
        "- **What works:** search, record lookup and reason codes are deterministic or retrieval-based, so they",
        "  score the same with any model. Both templates run through the same code; only the template folder differs.",
        ("- **What fails and why:** see the worst failures above. Change Watch quality depends on the model: the fake"
         "\n  provider extracts no requirements, so its unit and quote numbers stay at zero." if fake else
         "- **What fails and why:** see the worst failures above. Change Watch and root causes depend on the model:"
         "\n  it sometimes maps a requirement to the wrong unit or stakeholder group, which a reviewer then corrects."),
        "- **Payments vs university:** the university template was written second with fewer change cases",
        "  (3 vs 5), so one miss moves its percentages more. Compare the two columns in each table.",
        "- **Safety:** masking leaks counts unmasked IBANs, account numbers, cards, national IDs, phones or emails",
        "  in any prompt sent to the model or any draft reply. The target is 0.",
        "",
        "## Ideas to improve",
        "",
        "1. Add more change cases for the university template so its numbers are as stable as the payments ones.",
        "2. Use hybrid (keyword + vector) search for exact codes such as reason codes and course IDs.",
        "3. Add a second model pass that checks each impact has a retrieved source before it is shown.",
        "",
    ]
    return "\n".join(lines)
