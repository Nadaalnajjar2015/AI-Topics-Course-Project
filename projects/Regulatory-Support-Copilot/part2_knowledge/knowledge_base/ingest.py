"""Ingestion interface for early integration; this stub builds no index."""
import argparse

from part1_templates.tools.templates import list_templates, load_template


def ingest_all(template_id: str | None = None) -> dict:
    """Describe the selected templates without claiming ingestion occurred."""
    templates = list_templates() if template_id is None else [load_template(template_id)]
    return {template.id: {"status": "stub", "collection": f"kb_{template.id}",
                          "files_read": 0, "chunks_by_doc_type": {}, "seconds": 0.0}
            for template in templates}


def _main() -> None:
    parser = argparse.ArgumentParser(description="Ingestion stub: no index is built yet.")
    parser.add_argument("--template", help="Template ID; omit to list all templates")
    for identifier, summary in ingest_all(parser.parse_args().template).items():
        print(f"{identifier}: stub; no index built ({summary['collection']})")


if __name__ == "__main__":
    _main()
