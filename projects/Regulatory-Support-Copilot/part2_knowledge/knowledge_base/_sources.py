"""Load the documented template sources; records, open requests and eval stay out."""
import json
import os
from pathlib import Path
import re

from part1_templates.tools.changes import parse_change
from part1_templates.tools.directory import list_stakeholders, list_units
from part1_templates.tools.templates import load_template
from part2_knowledge.common.config import PROJECT_ROOT, settings
from part2_knowledge.knowledge_base.chunking import Chunk, _make_chunks, chunk_markdown


def _source(path: Path) -> str:
    return Path(os.path.relpath(path, PROJECT_ROOT)).as_posix()


def _readable(value) -> str:
    if isinstance(value, dict):
        return "\n".join(f"{key.replace('_', ' ')}: {_readable(item)}" for key, item in value.items())
    if isinstance(value, list):
        return "; ".join(_readable(item) for item in value)
    return "none" if value is None else str(value)


def _unit_for_file(path: Path, units) -> dict:
    matches = [unit.unit_id for unit in units
               if re.search(rf"(?<![A-Za-z0-9]){re.escape(unit.unit_id)}(?![A-Za-z0-9])", path.stem)]
    return {"unit_id": matches[0]} if len(matches) == 1 else {}


def _entry_chunks(rows, path, template_id, doc_type, id_key, metadata_keys):
    chunks = []
    for index, row in enumerate(rows):
        location = str(row.get(id_key, f"{doc_type} {index + 1}"))
        metadata = {key: row[key] for key in metadata_keys if row.get(key) is not None}
        entries = _make_chunks([(location, _readable(row))], _source(path), template_id,
                               path.stem.replace("_", " "), doc_type, metadata)
        for chunk in entries:
            chunks.append(Chunk(f"{_source(path)}#{len(chunks)}", chunk.text, chunk.metadata))
    return chunks


def _load_chunks(template_id: str):
    template = load_template(template_id)
    root = (settings.templates_dir / template.id).resolve()
    reason_path = (root / template.reason_codes_doc).resolve()
    if not reason_path.is_relative_to(root):
        raise ValueError(f"Reason-code document for '{template.id}' must stay inside its template folder.")
    if not reason_path.is_file():
        raise FileNotFoundError(f"Reason-code document not found: {reason_path}")
    units = list_units(template.id)
    chunks, files = [], set()
    for path in sorted(set((root / "documents").glob("*.md")) | {reason_path}):
        chunks.extend(chunk_markdown(path.read_text(encoding="utf-8"), _source(path), template.id,
                                     metadata=_unit_for_file(path, units), reason_codes=path == reason_path))
        files.add(path)
    for name, rows, kind, id_key, keys in [
        ("units.json", [unit.model_dump() for unit in units], "unit", "unit_id", ("unit_id",)),
        ("stakeholders.json", [group.model_dump() for group in list_stakeholders(template.id)],
         "stakeholder", "stakeholder_id", ("stakeholder_id",)),
    ]:
        path = root / name
        chunks.extend(_entry_chunks(rows, path, template.id, kind, id_key, keys))
        files.add(path)
    for name, key, kind, id_key, keys in [
        ("past_requests.json", "requests", "past_request", "request_id", ("reason_code",)),
        ("past_action_items.json", "action_items", "past_action_item", "action_id", ("unit_id", "change_id")),
    ]:
        path = root / "history" / name
        rows = json.loads(path.read_text(encoding="utf-8"))[key]
        chunks.extend(_entry_chunks(rows, path, template.id, kind, id_key, keys))
        files.add(path)
    for path in sorted((root / "changes").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        document = parse_change(text, template.id)
        metadata = {"change_id": document.change_id, "published": document.published.isoformat(),
                    "scope": document.scope}
        if document.effective:
            metadata["effective"] = document.effective.isoformat()
        chunks.extend(chunk_markdown(text, _source(path), template.id, "change", metadata, numbered=True))
        files.add(path)
    return chunks, len(files)
