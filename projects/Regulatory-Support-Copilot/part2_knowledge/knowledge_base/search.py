"""Contract-example search stub; no ranking or vector database is used yet."""
from copy import deepcopy

from contracts.schemas import SearchResult
from part1_templates.tools.templates import load_template


def search(query: str, k: int = 5, filters: dict | None = None,
           template_id: str | None = None) -> list[SearchResult]:
    """Return at most the contract example, only within its owning template."""
    template = load_template(template_id)
    if k < 0:
        raise ValueError("k must be nonnegative.")
    result = SearchResult.model_validate(deepcopy(SearchResult.model_config["json_schema_extra"]["example"]))
    if k == 0 or result.metadata.get("template_id") != template.id:
        return []
    fields = {**result.metadata, "source": result.source, "doc_type": result.doc_type,
              "location": result.location}
    if any(key not in fields or fields[key] != value for key, value in (filters or {}).items()):
        return []
    return [result]
