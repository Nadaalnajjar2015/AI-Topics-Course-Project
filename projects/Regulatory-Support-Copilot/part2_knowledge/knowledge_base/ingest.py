"""Rebuild one cosine Chroma collection per discovered organization template."""
import argparse
from collections import Counter
from time import perf_counter

from chromadb.errors import NotFoundError

from part1_templates.tools.templates import list_templates, load_template
from part2_knowledge.knowledge_base import _store
from part2_knowledge.knowledge_base._sources import _load_chunks


def ingest_all(template_id: str | None = None) -> dict:
    """Rebuild selected/all collections and return file/chunk counts and timings."""
    templates = list_templates() if template_id is None else [load_template(template_id)]
    summaries = {}
    client = _store._client()
    embedding_function = _store._embedding_function()
    for template in templates:
        started = perf_counter()
        chunks, files_read = _load_chunks(template.id)
        # Prepare embeddings before removing the previous index if a source/model fails.
        embeddings = embedding_function(input=[chunk.text for chunk in chunks]) if chunks else []
        name = f"kb_{template.id}"
        try:
            client.delete_collection(name)
        except NotFoundError:
            pass
        collection = client.create_collection(name, embedding_function=embedding_function,
                                              configuration={"hnsw": {"space": "cosine"}})
        for start in range(0, len(chunks), 100):
            batch = chunks[start:start + 100]
            collection.add(ids=[chunk.id for chunk in batch], documents=[chunk.text for chunk in batch],
                           metadatas=[chunk.metadata for chunk in batch], embeddings=embeddings[start:start + 100])
        summaries[template.id] = {"status": "ready" if chunks else "empty", "collection": name,
                                  "files_read": files_read, "chunks": len(chunks),
                                  "chunks_by_doc_type": dict(sorted(Counter(
                                      chunk.metadata["doc_type"] for chunk in chunks).items())),
                                  "seconds": round(perf_counter() - started, 3)}
    return summaries


def _main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild the knowledge index for one or all templates.")
    parser.add_argument("--template", help="Template ID; omit to rebuild all templates")
    try:
        summaries = ingest_all(parser.parse_args().template)
    except (KeyError, ValueError, FileNotFoundError) as exc:
        parser.error(str(exc))
    for identifier, summary in summaries.items():
        counts = ", ".join(f"{kind}={count}" for kind, count in summary["chunks_by_doc_type"].items())
        print(f"{identifier}: {summary['files_read']} files, {summary['chunks']} chunks "
              f"({counts}); {summary['seconds']:.3f}s; {summary['collection']}")


if __name__ == "__main__":
    _main()
