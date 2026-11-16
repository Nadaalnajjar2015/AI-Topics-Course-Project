"""Isolated QA server: the production entry point with its own DB, index and Part 1 state.

    python tests/qa/launch_qa_server.py        # http://127.0.0.1:8100, password qa-pass-123

Data lives in runtime/qa/ (git-ignored); delete that folder for a fresh run. Uses the fake
model unless QA_PROVIDER=groq. Never point the QA suites at the production site.
"""
import os
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
QA = PROJECT / "runtime" / "qa"
QA.mkdir(parents=True, exist_ok=True)
os.environ.update({
    "APP_DB": str(QA / "app.db"), "CHROMA_DIR": str(QA / "chroma"),
    "SITE_PASSWORD": os.environ.get("QA_PASSWORD", "qa-pass-123"),
    "LLM_PROVIDER": os.environ.get("QA_PROVIDER", "fake"), "PORT": "8100",
})
sys.path.insert(0, str(PROJECT))
os.chdir(PROJECT)

from part1_templates.tools import _files  # noqa: E402

_files._RUNTIME_ROOT = QA / "part1_runtime"
from part5_web import serve  # noqa: E402

serve.main()
