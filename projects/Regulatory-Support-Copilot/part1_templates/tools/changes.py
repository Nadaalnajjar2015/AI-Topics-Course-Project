"""Read stored changes and parse pasted YAML-front-matter documents."""
import yaml

from contracts.schemas import ChangeDocument
from part1_templates.tools._files import template_dir
from part1_templates.tools.templates import load_template


def parse_change(text, template_id=None) -> ChangeDocument:
    """Parse the header without executing or interpreting document instructions."""
    template_id = load_template(template_id).id
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("Change document must start with a YAML header delimited by ---")
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as exc:
        raise ValueError("Change document YAML header has no closing ---") from exc
    header = yaml.safe_load("\n".join(lines[1:end]))
    if not isinstance(header, dict):
        raise ValueError("Change document YAML header must be a mapping")
    document = ChangeDocument.model_validate({**header, "text": text})
    if document.template_id != template_id:
        raise ValueError(f"Change belongs to template {document.template_id}, not {template_id}")
    if document.effective is not None and document.effective < document.published:
        raise ValueError("Change effective date must not precede publication")
    return document


def list_changes(template_id=None) -> list[ChangeDocument]:
    """List changes by ID, preserving their full text for citations."""
    template_id = load_template(template_id).id
    return [parse_change(path.read_text(encoding="utf-8"), template_id)
            for path in sorted((template_dir(template_id) / "changes").glob("*.md"))]


def get_change(change_id, template_id=None) -> ChangeDocument:
    """Look up a change without using an untrusted ID as a file path."""
    template_id = load_template(template_id).id
    for document in list_changes(template_id):
        if document.change_id == change_id:
            return document
    raise KeyError(f"Change {change_id} not found in template {template_id}")
