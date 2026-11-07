"""Search only the selected template's cosine collection, with equality filters."""
import math

from chromadb.errors import NotFoundError

from contracts.schemas import SearchResult
from part1_templates.tools.templates import load_template
from part2_knowledge.knowledge_base import _store


def _where(filters: dict | None, template_id: str) -> dict:
    conditions = [{"template_id": template_id}]
    for key, value in (filters or {}).items():
        if not isinstance(key, str) or not key or key.startswith("$"):
            raise ValueError("Filter keys must be nonempty metadata names, not operators.")
        if not isinstance(value, (str, int, float, bool)) or isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"Filter '{key}' must have a finite scalar value.")
        conditions.append({key: value})
    return conditions[0] if len(conditions) == 1 else {"$and": conditions}


def search(query: str, k: int = 5, filters: dict | None = None,
           template_id: str | None = None) -> list[SearchResult]:
    """Return up to k cited chunks; missing/empty collections name the rebuild command."""
    template = load_template(template_id)
    if not isinstance(k, int) or isinstance(k, bool) or k < 0:
        raise ValueError("k must be a nonnegative integer.")
    if not query.strip():
        raise ValueError("Search query must not be empty.")
    where = _where(filters, template.id)
    if k == 0:
        return []
    message = (f"Knowledge base for '{template.id}' is empty. "
               "Run python -m part2_knowledge.knowledge_base.ingest")
    try:
        collection = _store._client().get_collection(f"kb_{template.id}",
                                                     embedding_function=_store._embedding_function())
    except NotFoundError as exc:
        raise RuntimeError(message) from exc
    count = collection.count()
    if not count:
        raise RuntimeError(message)
    found = collection.query(query_texts=[query], n_results=min(k, count), where=where,
                              include=["documents", "metadatas", "distances"])
    results = []
    for text, metadata, distance in zip(found["documents"][0], found["metadatas"][0], found["distances"][0]):
        if not math.isfinite(distance):
            raise RuntimeError("Knowledge base returned a non-finite cosine distance.")
        score = round(max(0.0, min(1.0, 1 - distance)), 3)
        results.append(SearchResult(text=text, source=metadata["source"], doc_type=metadata["doc_type"],
                                    location=metadata["location"], score=score, metadata=dict(metadata)))
    return results
