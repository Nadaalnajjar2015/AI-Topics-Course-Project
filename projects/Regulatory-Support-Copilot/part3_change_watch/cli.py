"""Run the three agents synchronously and emit one JSON envelope."""
import argparse
import json
import sys

from part1_templates.tools.changes import get_change
from part2_knowledge.common.config import settings
from part2_knowledge.common.llm import LLMError
from part2_knowledge.common.privacy import PrivacyError, mask_text
from part3_change_watch.watcher import summarize
from part3_change_watch.impact import analyze
from part3_change_watch.action_planner import plan


def run(doc):
    summary = summarize(doc)
    report = analyze(summary)
    actions = plan(summary, report)
    return {"summary": summary.model_dump(mode="json"), "impact_report": report.model_dump(mode="json"),
            "action_items": [item.model_dump(mode="json") for item in actions]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("change_id")
    parser.add_argument("--template", default=None, help="Template ID; defaults to ACTIVE_TEMPLATE.")
    args = parser.parse_args(argv)
    try:
        doc = get_change(args.change_id, template_id=args.template)
        outputs = run(doc)
        outputs["provider"] = settings.llm_provider
        outputs["interface_only"] = settings.llm_provider == "fake"
        if outputs["interface_only"]:
            print("FAKE PROVIDER: interface development only; no genuine extraction or evaluation.", file=sys.stderr)
        print(json.dumps(outputs, indent=2, ensure_ascii=False))
        return 0
    except (KeyError, ValueError) as exc:
        print(f"Change Watch input/output error: {mask_text(str(exc))}", file=sys.stderr)
        return 2
    except (LLMError, PrivacyError) as exc:
        print(f"Change Watch stopped: {mask_text(str(exc))}", file=sys.stderr)
        return 3
    except RuntimeError:
        print("Knowledge base unavailable; run python -m part2_knowledge.knowledge_base.ingest. "
              "Check the selected template and privacy-policy version.", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
