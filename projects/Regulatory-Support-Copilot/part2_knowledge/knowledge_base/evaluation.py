"""Exact-source Hit@5 evaluation with per-query, privacy-safe reporting."""
from pathlib import PurePosixPath
from time import perf_counter

from part2_knowledge.common.privacy import mask_text
from part2_knowledge.knowledge_base.search import search

TARGET_HIT_AT_5 = 0.8


def _source_path(value: str) -> str:
    path = PurePosixPath(value.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Evaluation sources must be project-relative paths without '..'.")
    return path.as_posix()


def evaluate_search(cases: list[dict], template_id: str) -> dict:
    """Run every case unfiltered, count only the first five exact source paths."""
    if not isinstance(cases, list) or not cases:
        raise ValueError("Search evaluation must contain a nonempty cases list.")
    started = perf_counter()
    rows = []
    for index, case in enumerate(cases, 1):
        if not isinstance(case, dict) or any(not isinstance(case.get(key), str) or not case[key].strip()
                                             for key in ("query", "expected_source")):
            raise ValueError(f"Evaluation case {index} needs nonempty query and expected_source strings.")
        query = mask_text(case["query"])
        expected = mask_text(_source_path(case["expected_source"]))
        results = search(query, k=5, template_id=template_id)[:5]
        if any(result.metadata.get("template_id") != template_id for result in results):
            raise RuntimeError("Search evaluation received evidence belonging to a different template.")
        sources = [mask_text(_source_path(result.source)) for result in results]
        rank = sources.index(expected) + 1 if expected in sources else None
        rows.append({"query": query, "expected_source": expected, "sources": sources,
                     "rank": rank, "hit": rank is not None})
    hits = sum(row["hit"] for row in rows)
    rate = hits / len(rows)
    return {"template_id": template_id, "hits": hits, "total": len(rows), "hit_at_5": rate,
            "passed": rate >= TARGET_HIT_AT_5, "cases": rows,
            "seconds": round(perf_counter() - started, 3)}


def format_search_report(report: dict) -> str:
    """Show every query's outcome and all returned sources for each miss."""
    state = "PASS" if report["passed"] else "FAIL"
    lines = [f"{report['template_id']}: Hit@5 {report['hits']}/{report['total']} = "
             f"{report['hit_at_5']:.1%}; target {TARGET_HIT_AT_5:.0%}: {state}",
             "status | query | expected source | rank / returned sources"]
    for row in report["cases"]:
        outcome = "HIT" if row["hit"] else "MISS"
        evidence = f"rank {row['rank']}" if row["hit"] else ", ".join(row["sources"]) or "no results"
        lines.append(f"{outcome} | {row['query']} | {row['expected_source']} | {evidence}")
    return mask_text("\n".join(lines))
