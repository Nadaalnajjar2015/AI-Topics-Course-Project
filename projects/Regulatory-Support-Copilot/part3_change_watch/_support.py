"""Private prompt, evidence and draft schemas; no provider clients here."""
import json
from pathlib import Path, PurePosixPath

from pydantic import BaseModel, Field

from contracts.schemas import Requirement
from part2_knowledge.common.prompting import load_prompt, render


def prompt(name, template):
    return render(load_prompt(Path(__file__).parent / "prompts" / f"{name}.md"), template)


def data_tag(name, value):
    # JSON escapes prevent source text from closing data tags or opening new ones.
    encoded = json.dumps(value, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e")
    return f"<{name}>\n{encoded}\n</{name}>"


def verified_sources(sources, template_id, doc_type):
    """Fail closed on foreign, missing-ownership or wrong-type citations."""
    prefix = ("part1_templates", "templates", template_id)
    accepted = []
    for source in sources:
        parts = PurePosixPath(source.source).parts
        if (source.metadata.get("template_id") != template_id or source.doc_type != doc_type
                or parts[:3] != prefix or ".." in parts):
            raise ValueError("Retrieved citation has invalid template ownership or document type.")
        accepted.append(source)
    return accepted


def merge_sources(sources):
    unique = {json.dumps(s.model_dump(mode="json"), sort_keys=True): s for s in sources}
    return [unique[key] for key in sorted(unique)]


class _ClosedResponse(BaseModel):
    model_config = {"extra": "forbid"}


class ExtractedRequirement(_ClosedResponse):
    description: str = Field(min_length=1, description="One concrete obligation or recommendation.")
    category: Requirement.model_fields["category"].annotation = Field(description="General category.")
    mandatory: bool = Field(description="Whether the source imposes an obligation.")
    source_quote: str = Field(min_length=1, description="Exact source sentence or clause.")
    source_location: str = Field(description="Section identifier from the supplied sections.")


class Extraction(_ClosedResponse):
    summary_text: str = Field(description="Two or three factual sentences; no invented clauses.")
    effective_date: str | None = Field(description="ISO date only if explicit in source, else null.")
    effective_quote: str | None = Field(description="Exact sentence stating that effective date, else null.")
    requirements: list[ExtractedRequirement] = Field(description="Separate concrete requirements, excluding background.")
    model_config = {"json_schema_extra": {"example": {
        "summary_text": "Fake interface response; no extraction was performed.",
        "effective_date": None, "effective_quote": None, "requirements": [],
    }}}


class UnitChoice(_ClosedResponse):
    unit_id: str = Field(description="One ID from supplied candidates only.")
    reason: str = Field(min_length=1, description="Why the requirement affects this unit.")
    evidence_indices: list[int] = Field(description="Zero-based indices of actual supporting passages.")
    raise_severity: bool = Field(description="Request at most one severity increase.")
    escalation_reason: str = Field(description="Evidence-based reason for increasing severity, or empty.")


class UnitSelection(_ClosedResponse):
    units: list[UnitChoice] = Field(description="Distinct affected units with supporting passage indices.")
    model_config = {"json_schema_extra": {"example": {"units": []}}}


class DraftCheck(_ClosedResponse):
    steps: list[str] = Field(min_length=1, description="Concrete ordered verification steps.")
    expected: str = Field(min_length=1, description="Observable expected outcome.")


class DraftAction(_ClosedResponse):
    title: str = Field(min_length=1, description="Specific title for this unit's work.")
    description: str = Field(min_length=1, description="Specific required changes citing every requirement ID.")
    owner_role: str = Field(min_length=1, description="Accountable role, not an invented person.")
    checks: list[DraftCheck] = Field(min_length=2, max_length=4, description="Two to four useful verifiable checks.")
    model_config = {"json_schema_extra": {"example": {
        "title": "Fake interface draft", "description": "No model-generated plan is available.",
        "owner_role": "Reviewer", "checks": [
            {"steps": ["Inspect the proposed configuration."], "expected": "Configuration is available for review."},
            {"steps": ["Review the linked requirement."], "expected": "The reviewer records whether it is satisfied."}],
    }}}
