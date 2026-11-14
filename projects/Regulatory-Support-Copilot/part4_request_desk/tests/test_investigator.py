import pytest

from contracts.schemas import Record, Request, SearchResult
from part1_templates.tools.templates import load_template
from part4_request_desk import investigator


def _request(template_id: str, body: str, *, request_id: str = "TEST-REQ", person_id: str | None = None,
             item: str | None = None) -> Request:
    example = Request.model_config["json_schema_extra"]["example"]
    return Request.model_validate({
        **example,
        "request_id": request_id,
        "template_id": template_id,
        "person_id": person_id or ("BANK-C" if template_id == "payments" else "S-2291"),
        "body": body,
        "item": item,
    })


def _record(
    template_id: str,
    person_id: str,
    item: str,
    unit_id: str,
    status: str,
    reason_code: str | None,
    timestamp: str = "2026-03-02T09:12:03",
) -> Record:
    return Record.model_validate({
        "record_id": f"REC-{template_id}-{item}-{timestamp}",
        "template_id": template_id,
        "timestamp": timestamp,
        "person_id": person_id,
        "unit_id": unit_id,
        "item": item,
        "status": status,
        "reason_code": reason_code,
        "detail": "Fictional record detail for testing.",
    })


def _source(template_id: str, doc_type: str, *, reason_code: str | None = None) -> SearchResult:
    if doc_type == "reason_codes":
        relative_path = (
            "documents/reason_codes.md" if template_id == "payments"
            else "documents/registration_rules.md"
        )
        location = reason_code or "test-code"
    else:
        relative_path = f"documents/{doc_type}.md"
        location = "test-section"
    metadata: dict[str, object] = {"template_id": template_id}
    if reason_code is not None:
        metadata["reason_code"] = reason_code
    return SearchResult.model_validate({
        "text": "Fictional source text supporting the test.",
        "source": f"part1_templates/templates/{template_id}/{relative_path}",
        "doc_type": doc_type,
        "location": location,
        "score": 0.9,
        "metadata": metadata,
    })


def _install_fakes(
    monkeypatch: pytest.MonkeyPatch,
    template_id: str,
    records: list[Record],
    *,
    sources: dict[str, list[SearchResult]] | None = None,
    extracted_text: str | None = None,
) -> tuple[list[dict[str, object]], list[tuple[str, dict[str, str], str, int]]]:
    record_calls: list[dict[str, object]] = []
    search_calls: list[tuple[str, dict[str, str], str, int]] = []
    sources = sources or {}

    def fake_records(**kwargs: object) -> list[Record]:
        record_calls.append(kwargs)
        assert kwargs["template_id"] == template_id
        return records

    def fake_search(
        query: str,
        filters: dict[str, str],
        template_id_arg: str,
        *,
        k: int = 2,
    ) -> list[SearchResult]:
        search_calls.append((query, filters, template_id_arg, k))
        assert template_id_arg == template_id
        return sources.get(filters["doc_type"], [])

    def fake_complete_json(system: str, user: str, schema: type) -> object:
        if schema is investigator._ItemExtraction:
            return schema(matched_text=extracted_text)
        assert schema is investigator._Narrative
        return schema(
            root_cause="The supplied evidence explains the request.",
            draft_reply="The available information is summarized here.",
        )

    monkeypatch.setattr(investigator, "search_records", fake_records)
    monkeypatch.setattr(investigator, "_search_knowledge", fake_search)
    monkeypatch.setattr(investigator.llm, "complete_json", fake_complete_json)
    return record_calls, search_calls


@pytest.mark.parametrize(
    ("template_id", "person_id", "item", "unit_id", "status", "reason_code", "request_id"),
    [
        ("payments", "BANK-C", "7731", "ACH", "REJECTED", "AC04", "P-REQ-007"),
        ("university", "S-2291", "SE301", "SE-BSc", "BLOCKED", "PREREQ_MISSING", "U-REQ-007"),
    ],
)
def test_investigate_reports_rejected_or_blocked_fixture(
    monkeypatch: pytest.MonkeyPatch,
    template_id: str,
    person_id: str,
    item: str,
    unit_id: str,
    status: str,
    reason_code: str,
    request_id: str,
) -> None:
    record = _record(template_id, person_id, item, unit_id, status, reason_code)
    sources = {
        "reason_codes": [_source(template_id, "reason_codes", reason_code=reason_code)],
        "past_request": [_source(template_id, "past_request")],
    }
    record_calls, search_calls = _install_fakes(monkeypatch, template_id, [record], sources=sources)
    request = _request(
        template_id,
        "Why was payment 7731 rejected?" if template_id == "payments"
        else "Why can't I register for SE301?",
        request_id=request_id,
        person_id=person_id,
    )

    result = investigator.investigate(request)

    assert result.request_id == request_id
    assert result.item == item
    assert result.reason_code == reason_code
    assert result.evidence == [record]
    assert result.confidence == "high"
    assert result.escalate is False
    expected_signature = (
        "Support Team, Cedar Payment Systems"
        if template_id == "payments" else "Registrar's Office"
    )
    assert result.draft_reply.endswith(expected_signature)
    assert {source.doc_type for source in result.sources} == {"reason_codes", "past_request"}
    assert record_calls == [{"person_id": person_id, "item": item, "template_id": template_id}]
    assert [(filters["doc_type"], template) for _, filters, template, _ in search_calls] == [
        ("reason_codes", template_id),
        ("past_request", template_id),
    ]


@pytest.mark.parametrize(
    ("template_id", "person_id", "item", "unit_id", "status", "body"),
    [
        ("payments", "BANK-A", "8820", "CHQ", "SETTLED", "Did payment 8820 go through?"),
        ("university", "S-2288", "BUS101", "BUS-BBA", "COMPLETED", "Did BUS101 registration go through?"),
    ],
)
def test_investigate_explains_successful_record(
    monkeypatch: pytest.MonkeyPatch,
    template_id: str,
    person_id: str,
    item: str,
    unit_id: str,
    status: str,
    body: str,
) -> None:
    record = _record(template_id, person_id, item, unit_id, status, None)
    record_calls, _ = _install_fakes(
        monkeypatch, template_id, [record],
        sources={"past_request": [_source(template_id, "past_request")]},
    )

    result = investigator.investigate(_request(template_id, body, person_id=person_id))

    assert result.item == item
    assert result.reason_code is None
    assert result.evidence == [record]
    assert result.confidence == "medium"
    assert result.escalate is False
    assert record_calls[0]["item"] == item


@pytest.mark.parametrize(
    ("template_id", "body"),
    [
        ("payments", "Please locate payment 99999."),
        ("university", "Please check CS999: there is no registration result."),
    ],
)
def test_unknown_reference_escalates_with_low_confidence(
    monkeypatch: pytest.MonkeyPatch,
    template_id: str,
    body: str,
) -> None:
    record_calls, _ = _install_fakes(
        monkeypatch, template_id, [],
        sources={"past_request": [_source(template_id, "past_request")]},
    )

    result = investigator.investigate(_request(template_id, body))

    assert result.item == ("99999" if template_id == "payments" else "CS999")
    assert result.reason_code is None
    assert result.evidence == []
    assert result.confidence == "low"
    assert result.escalate is True
    assert record_calls[0]["item"] == result.item


@pytest.mark.parametrize(
    ("template_id", "body"),
    [
        ("payments", "What is the cheque cut-off time?"),
        ("university", "What is the maximum absence allowed?"),
    ],
)
def test_general_question_uses_template_documents_without_records(
    monkeypatch: pytest.MonkeyPatch,
    template_id: str,
    body: str,
) -> None:
    _, search_calls = _install_fakes(
        monkeypatch, template_id, [],
        sources={
            "document": [_source(template_id, "document")],
            "past_request": [_source(template_id, "past_request")],
        },
    )

    result = investigator.investigate(_request(template_id, body))

    assert result.item is None
    assert result.reason_code is None
    assert result.evidence == []
    assert result.confidence == "medium"
    assert result.escalate is False
    assert {source.doc_type for source in result.sources} == {"document", "past_request"}
    assert ("document", template_id) in [
        (filters["doc_type"], selected_template)
        for _, filters, selected_template, _ in search_calls
    ]


@pytest.mark.parametrize(
    ("template_id", "person_id", "body", "unit_id", "selected_item", "selected_code"),
    [
        ("payments", "BANK-C", "Our instant payment transfers keep failing.", "IPS", "8801", "AM04"),
        ("university", "S-2291", "I cannot register in software engineering; it keeps failing.", "SE-BSc", "SE301", "PREREQ_MISSING"),
    ],
)
def test_no_item_uses_person_records_in_named_unit_and_latest_failure(
    monkeypatch: pytest.MonkeyPatch,
    template_id: str,
    person_id: str,
    body: str,
    unit_id: str,
    selected_item: str,
    selected_code: str,
) -> None:
    latest = _record(
        template_id, person_id, selected_item, unit_id, "BLOCKED", selected_code,
        timestamp="2026-03-03T11:00:00",
    )
    earlier = _record(
        template_id, person_id, "OLDER", unit_id, "REJECTED", "OLD_CODE",
        timestamp="2026-03-01T11:00:00",
    )
    other_unit = _record(
        template_id, person_id, "OTHER", "ACH" if template_id == "payments" else "BUS-BBA",
        "REJECTED", "OTHER_CODE", timestamp="2026-03-04T11:00:00",
    )
    sources = {
        "reason_codes": [_source(template_id, "reason_codes", reason_code=selected_code)],
        "past_request": [_source(template_id, "past_request")],
    }
    record_calls, _ = _install_fakes(
        monkeypatch, template_id, [earlier, latest, other_unit], sources=sources
    )

    result = investigator.investigate(_request(template_id, body, person_id=person_id))

    assert result.item is None
    assert result.reason_code == selected_code
    assert result.evidence == [latest]
    assert result.confidence == "high"
    assert result.escalate is False
    assert record_calls == [{"person_id": person_id, "item": None, "template_id": template_id}]


@pytest.mark.parametrize(
    ("template_id", "item", "phrases"),
    [
        ("payments", "7731", [
            "payment 7731",
            "PAYMENT #7731",
            "ref 7731",
            "ref=7731",
            "transfer 7731",
            "transfer#7731",
        ]),
        ("university", "SE301", [
            "SE301",
            "Course SE301",
            "Can I register for SE301?",
            "se301 registration",
            "Please review: SE301",
            "The course code is SE301.",
        ]),
    ],
)
def test_item_patterns_cover_common_writing_styles(
    monkeypatch: pytest.MonkeyPatch,
    template_id: str,
    item: str,
    phrases: list[str],
) -> None:
    for phrase in phrases:
        record = _record(
            template_id,
            "BANK-C" if template_id == "payments" else "S-2291",
            item,
            "ACH" if template_id == "payments" else "SE-BSc",
            "REJECTED",
            "AC04" if template_id == "payments" else "PREREQ_MISSING",
        )
        record_calls, _ = _install_fakes(
            monkeypatch, template_id, [record],
            sources={"past_request": [_source(template_id, "past_request")]},
        )

        result = investigator.investigate(_request(template_id, phrase))

        assert result.item == item
        assert record_calls[0]["item"] == item


def test_item_llm_fallback_is_pattern_checked_and_quote_checked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request("payments", "Please review the payment reference mentioned above: payment 7731.")
    record = _record("payments", "BANK-C", "7731", "ACH", "REJECTED", "AC04")
    record_calls, _ = _install_fakes(
        monkeypatch,
        "payments",
        [record],
        sources={"past_request": [_source("payments", "past_request")]},
        extracted_text="the payment reference mentioned above: payment 7731",
    )

    result = investigator.investigate(request)

    assert result.item == "7731"
    assert record_calls[0]["item"] == "7731"


def test_invalid_item_llm_fallback_does_not_create_a_reference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record_calls, _ = _install_fakes(
        monkeypatch,
        "payments",
        [],
        sources={"past_request": [_source("payments", "past_request")]},
        extracted_text="payment 99999",
    )

    result = investigator.investigate(
        _request("payments", "I cannot find the reference in my records.")
    )

    assert result.item is None
    assert result.evidence == []
    assert result.confidence == "low"
    assert result.escalate is True
    assert record_calls[0]["item"] is None


def test_reason_code_without_matching_source_has_medium_confidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = _record("payments", "BANK-C", "7731", "ACH", "REJECTED", "UNKNOWN_CODE")
    _install_fakes(
        monkeypatch,
        "payments",
        [record],
        sources={"past_request": [_source("payments", "past_request")]},
    )

    result = investigator.investigate(
        _request("payments", "Why was payment 7731 rejected?", person_id="BANK-C")
    )

    assert result.reason_code == "UNKNOWN_CODE"
    assert result.confidence == "medium"
    assert result.escalate is False


def test_template_sources_must_belong_to_selected_organization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wrong_template_source = _source("university", "past_request")
    _install_fakes(
        monkeypatch,
        "payments",
        [],
        sources={"past_request": [wrong_template_source]},
    )

    with pytest.raises(ValueError, match="outside the requested template"):
        investigator.investigate(_request("payments", "Please locate payment 99999."))
