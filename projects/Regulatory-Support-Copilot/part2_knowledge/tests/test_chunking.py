import pytest

from part2_knowledge.knowledge_base.chunking import chunk_markdown


def test_heading_split_context_and_metadata():
    text = "MOCK DATA – fictional, for a student prototype\n\n# Guide\n\n## First\nAlpha.\n\n## Second\nBeta."
    chunks = chunk_markdown(text, "documents/guide.md", "example", metadata={"unit_id": "UNIT-1"})
    assert [chunk.id for chunk in chunks] == ["documents/guide.md#0", "documents/guide.md#1"]
    assert [chunk.text for chunk in chunks] == ["[Guide – First] Alpha.", "[Guide – Second] Beta."]
    assert chunks[0].metadata == {"source": "documents/guide.md", "doc_type": "document",
                                  "location": "First", "template_id": "example", "unit_id": "UNIT-1"}


def test_long_sections_split_at_sentences_with_overlap_and_coverage():
    body = " ".join(f"Sentence {index:03d} has enough words to explain the process clearly."
                    for index in range(50))
    chunks = chunk_markdown(f"# Guide\n## Long\n{body}", "guide.md", "example")
    pieces = [chunk.text.split("] ", 1)[1] for chunk in chunks]
    assert len(pieces) > 1
    assert all(len(piece) <= 800 for piece in pieces)
    assert all(piece.endswith(".") for piece in pieces[:-1])
    assert all(left[-80:] in right for left, right in zip(pieces, pieces[1:]))
    assert all(f"Sentence {index:03d}" in " ".join(pieces) for index in range(50))
    assert all(chunk.metadata["location"] == "Long" for chunk in chunks)


def test_long_single_token_makes_progress_and_ids_are_stable():
    text = "# Guide\n## Long\n" + "x" * 1800
    first = chunk_markdown(text, "guide.md", "example")
    second = chunk_markdown(text, "guide.md", "example")
    assert first == second and len(first) == 3
    assert len({chunk.id for chunk in first}) == 3
    assert all(len(chunk.text.split("] ", 1)[1]) <= 800 for chunk in first)


def test_change_front_matter_and_numbered_sections():
    text = ("---\nchange_id: CHG-X-1\n---\nMOCK DATA – fictional, for a student prototype\n"
            "# New rule\n## Requirements\n1. First rule.\nContinuation.\n2. Second rule.\n"
            "3.1 A nested rule.\n## Background\nEarlier policy.")
    chunks = chunk_markdown(text, "change.md", "example", "change", numbered=True)
    assert [chunk.metadata["location"] for chunk in chunks] == [
        "Requirements / 1", "Requirements / 2", "Requirements / 3.1"]
    assert "Continuation." in chunks[0].text
    assert all("change_id:" not in chunk.text and "MOCK DATA" not in chunk.text for chunk in chunks)
    assert all("Earlier policy" not in chunk.text for chunk in chunks)


def test_reason_document_keeps_general_policy_and_code_sections_distinct():
    text = "# Rules\n## Credit limits\n18 credits.\n## PREREQ_MISSING\nComplete the prerequisite."
    chunks = chunk_markdown(text, "rules.md", "example", reason_codes=True)
    assert chunks[0].metadata["doc_type"] == "document"
    assert "reason_code" not in chunks[0].metadata
    assert chunks[1].metadata["doc_type"] == "reason_codes"
    assert chunks[1].metadata["reason_code"] == "PREREQ_MISSING"


@pytest.mark.parametrize("text", ["", "# Empty\n", "MOCK DATA – fictional, for a student prototype\n"])
def test_empty_sections_do_not_create_chunks(text):
    assert chunk_markdown(text, "empty.md", "example") == []
