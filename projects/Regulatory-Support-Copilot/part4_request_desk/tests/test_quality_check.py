import json
from pathlib import Path

import pytest

from contracts.schemas import Investigation, Request, Task
from part4_request_desk.tests import quality_check


def test_private_data_detector_catches_common_unmasked_values() -> None:
    for text in (
        "Reach me at s2291@student.example.",
        "IBAN JO00 MOCK 0000 0000 0000 0000 00",
        "Call +962 790 123 456",
        "National ID: 123456789012",
    ):
        assert quality_check._has_unmasked_private_data(text)
    assert not quality_check._has_unmasked_private_data(
        "The request was blocked because a prerequisite is missing."
    )


def test_evaluate_case_scores_expected_values_and_keywords() -> None:
    example = Investigation.model_config["json_schema_extra"]["example"]
    investigation = Investigation.model_validate({
        **example,
        "item": "7731",
        "reason_code": "AC04",
        "root_cause": "The account was closed before processing.",
        "draft_reply": "The reference was rejected. [REDACTED]",
        "escalate": False,
    })
    case = {
        "request_id": "P-REQ-007",
        "expected_item": "7731",
        "expected_reason_code": "AC04",
        "expected_escalate": False,
        "root_cause_keywords": ["closed", "account"],
    }

    result = quality_check._evaluate_case(case, investigation, 0.25)

    assert result.item_correct
    assert result.reason_code_correct
    assert result.escalation_correct
    assert result.keyword_matches == 2
    assert result.keyword_count == 2
    assert result.privacy_clean
    assert result.elapsed_seconds == 0.25


def test_run_template_reads_eval_and_uses_isolated_task_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    templates_dir = tmp_path / "templates"
    eval_dir = templates_dir / "payments" / "eval"
    eval_dir.mkdir(parents=True)
    (eval_dir / "request_eval.json").write_text(json.dumps({
        "cases": [{
            "request_id": "P-REQ-007",
            "expected_item": "7731",
            "expected_reason_code": "AC04",
            "expected_escalate": False,
            "root_cause_keywords": ["closed"],
        }]
    }), encoding="utf-8")
    request = Request.model_validate({
        **Request.model_config["json_schema_extra"]["example"],
        "request_id": "P-REQ-007",
        "template_id": "payments",
    })
    investigation = Investigation.model_validate({
        **Investigation.model_config["json_schema_extra"]["example"],
        "request_id": "P-REQ-007",
        "root_cause": "The account is closed.",
    })
    task = Task.model_validate({
        **Task.model_config["json_schema_extra"]["example"],
        "input_ref": "P-REQ-007",
        "status": "pending_review",
        "outputs": {"investigation": investigation.model_dump(mode="json")},
    })
    monkeypatch.setattr(quality_check.settings, "templates_dir", templates_dir)
    monkeypatch.setattr(quality_check, "list_requests", lambda template_id: [request])
    original_database = quality_check.store.settings.app_db
    evaluated_databases: list[Path] = []

    def fake_run_request_sync(_: Request) -> Task:
        database = Path(quality_check.store.settings.app_db)
        assert database.parent.exists()
        evaluated_databases.append(database)
        return task

    monkeypatch.setattr(quality_check, "run_request_sync", fake_run_request_sync)

    results = quality_check.run_template("payments")

    assert len(results) == 1
    assert results[0].request_id == "P-REQ-007"
    assert results[0].item_correct
    assert len(evaluated_databases) == 1
    assert evaluated_databases[0] != original_database
    assert not evaluated_databases[0].parent.exists()
    assert quality_check.store.settings.app_db == original_database


def test_quality_cli_refuses_to_report_fake_provider_as_real(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(quality_check.settings, "llm_provider", "fake")

    with pytest.raises(SystemExit) as exc_info:
        quality_check.main(["--template", "all"])

    assert exc_info.value.code == 2
