"""Heading-first, deterministic chunks with readable context and scalar metadata."""
from dataclasses import dataclass
from pathlib import PurePosixPath
import re

from part2_knowledge.common.privacy import mask_text


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    metadata: dict[str, str | int | float | bool]


def _split_long(text: str, size: int = 800, overlap: int = 100) -> list[str]:
    pieces = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundaries = list(re.finditer(r"[.!?]\s+", text[start + size // 2:end]))
            if boundaries:
                end = start + size // 2 + boundaries[-1].end()
            else:
                spaces = list(re.finditer(r"\s+", text[start + size // 2:end]))
                if spaces:
                    end = start + size // 2 + spaces[-1].end()
        if piece := text[start:end].strip():
            pieces.append(piece)
        if end == len(text):
            break
        start = max(start + 1, end - overlap)
    return pieces


def _make_chunks(sections, source, template_id, title, doc_type, metadata=None,
                 reason_codes=False) -> list[Chunk]:
    chunks = []
    for location, text in sections:
        context = {**(metadata or {}), "source": source, "doc_type": doc_type,
                   "location": location, "template_id": template_id}
        if reason_codes and re.fullmatch(r"[A-Z][A-Z0-9_]+", location):
            context.update(doc_type="reason_codes", reason_code=location)
        for piece in _split_long(text.strip()):
            chunks.append(Chunk(f"{source}#{len(chunks)}", f"[{title} – {location}] {piece}",
                                dict(context)))
    return chunks


def chunk_markdown(text: str, source: str, template_id: str, doc_type: str = "document",
                   metadata: dict | None = None, *, reason_codes: bool = False,
                   numbered: bool = False) -> list[Chunk]:
    """Split headings (or only numbered change clauses), then long overlapping bodies."""
    # Redact before splitting, so a private value crossing a chunk boundary cannot leak.
    text = mask_text(text)
    text = re.sub(r"\A---[^\n]*\n.*?\n---[^\n]*(?:\n|$)", "", text, count=1, flags=re.DOTALL)
    text = re.sub(r"(?m)^MOCK DATA[^\n]*(?:\n|$)", "", text)
    title_match = re.search(r"(?m)^# (.+)$", text)
    title = title_match[1].strip() if title_match else PurePosixPath(source).stem.replace("_", " ")
    heading = location = title
    sections, lines = [], []
    keep_section = not numbered
    for line in text.splitlines():
        heading_match = re.match(r"^#{1,2}\s+(.+)$", line)
        number_match = re.match(r"^(\d+(?:\.\d+)*)(?:\.)?\s+", line) if numbered else None
        if heading_match or number_match:
            if keep_section and "\n".join(lines).strip():
                sections.append((location, "\n".join(lines)))
            lines = []
            if heading_match:
                heading = location = heading_match[1].strip()
                keep_section = not numbered
                continue
            location = f"{heading} / {number_match[1]}"
            keep_section = True
        lines.append(line)
    if keep_section and "\n".join(lines).strip():
        sections.append((location, "\n".join(lines)))
    return _make_chunks(sections, source, template_id, title, doc_type, metadata, reason_codes)
