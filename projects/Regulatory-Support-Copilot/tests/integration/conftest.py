import pytest

from contracts.schemas import SearchResult
from part1_templates.tools.templates import load_template
from part2_knowledge.common.config import settings
from part2_knowledge.knowledge_base import search as search_module
from part3_change_watch import action_planner, impact
from part4_request_desk import investigator
from part4_request_desk.orchestrator import store


@pytest.fixture(autouse=True)
def isolated_fake_workflow(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(settings, "llm_provider", "fake")
    monkeypatch.setattr(settings, "active_template", "payments")
    monkeypatch.setattr(
        store,
        "settings",
        store.settings.model_copy(update={"app_db": tmp_path / "tasks.db"}),
    )

    def fake_search(
        query: str,
        k: int = 5,
        filters: dict[str, object] | None = None,
        template_id: str | None = None,
    ) -> list[SearchResult]:
        template = load_template(template_id)
        document_type = (filters or {}).get("doc_type", "document")
        if document_type == "past_action_item":
            return []
        if document_type == "reason_codes":
            reason_code = str((filters or {}).get("reason_code", ""))
            source = (
                f"part1_templates/templates/{template.id}/"
                f"{template.reason_codes_doc.replace(chr(92), '/')}"
            )
            return [SearchResult(
                text=f"Fictional guidance for {reason_code}.",
                source=source,
                doc_type="reason_codes",
                location=reason_code,
                score=0.9,
                metadata={"template_id": template.id, "reason_code": reason_code},
            )]
        if document_type == "past_request":
            return [SearchResult(
                text="Similar fictional request and reviewed response.",
                source=f"part1_templates/templates/{template.id}/history/past_requests.json",
                doc_type="past_request",
                location="fixture",
                score=0.8,
                metadata={"template_id": template.id},
            )]
        return []

    def investigator_search(
        query: str,
        filters: dict[str, str],
        template_id: str,
        *,
        k: int = 2,
    ) -> list[SearchResult]:
        return fake_search(query, k=k, filters=filters, template_id=template_id)

    monkeypatch.setattr(search_module, "search", fake_search)
    monkeypatch.setattr(impact, "search", fake_search)
    monkeypatch.setattr(action_planner, "search", fake_search)
    monkeypatch.setattr(investigator, "_search_knowledge", investigator_search)
