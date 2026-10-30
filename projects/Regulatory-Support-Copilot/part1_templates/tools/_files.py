"""Private JSON readers and atomic, template-isolated runtime state."""
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import RLock

from part1_templates.tools.templates import _PROJECT_ROOT, _templates_root, load_template

_RUNTIME_ROOT = _PROJECT_ROOT / "runtime"
_STATE_LOCK = RLock()


def template_dir(template_id=None) -> Path:
    return _templates_root() / load_template(template_id).id


def read_items(path: Path, key: str) -> list[dict]:
    """JSON data uses an envelope so the MOCK DATA note remains valid JSON."""
    return json.loads(path.read_text(encoding="utf-8"))[key]


def read_state(template_id=None) -> dict:
    identifier = load_template(template_id).id
    path = _RUNTIME_ROOT / identifier / "state.json"
    with _STATE_LOCK:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {"request_statuses": {}, "action_items": []}


def update_state(template_id, update) -> None:
    """Keep concurrent review updates together; replace the file atomically."""
    identifier = load_template(template_id).id
    with _STATE_LOCK:
        state = read_state(identifier)
        update(state)
        path = _RUNTIME_ROOT / identifier / "state.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(state, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
