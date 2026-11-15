"""Production entry point (used by Render): build the search index if missing, then serve.

    python -m part5_web.serve            # listens on 0.0.0.0:$PORT (default 8000)

Free hosts give a fresh, empty disk after every restart, so the knowledge index is rebuilt
when it is missing. Local development keeps using `uvicorn part5_web.app:app --reload`.
"""
import logging
import os
import subprocess
import sys

import uvicorn

from part1_templates.tools.templates import list_templates
from part5_web.pages import indexed_chunks

log = logging.getLogger("part5_web.serve")


def ensure_index() -> None:
    """Build the knowledge index for every template that has no chunks yet.

    Runs in a child process: embedding all documents needs far more memory than serving,
    and a free 512 MB instance only gets that memory back when the process exits.
    """
    for template in list_templates():
        if not indexed_chunks(template.id):
            log.warning("search index for %s is missing; building it", template.id)
            subprocess.run([sys.executable, "-m", "part2_knowledge.knowledge_base.ingest", "--template", template.id],
                           check=True)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    ensure_index()
    uvicorn.run("part5_web.app:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")),
                proxy_headers=True, forwarded_allow_ips="*")


if __name__ == "__main__":
    main()
