"""Shared data contracts for the Regulatory & Support Copilot (general version).

The code speaks in general words (template, unit, stakeholder, record, request, action item);
each organization's template.yaml gives them their labels.
Every model needs Field(description=...) on each field and one realistic example in
model_config = {"json_schema_extra": {"example": {...}}}.
Written on Contract Day (end of week 1); after that, changes need approval from all members.
See docs/00-Project-Guide.pdf, Section 8.
"""
from pydantic import BaseModel, Field  # noqa: F401  # type: ignore[import-not-found]

# --- Part 1: TemplateConfig, Unit, Stakeholder, ChangeDocument, Record, Request ---

from datetime import date, datetime
from typing import Literal


class TemplateConfig(BaseModel):
    """Organization vocabulary and the connector used by the common engine."""

    id: str = Field(description="Stable template folder identifier.")
    organization: str = Field(description="Fictional organization's display name.")
    languages: list[str] = Field(description="Supported language codes.")
    labels: dict[str, str] = Field(description="Organization labels for general concepts.")
    connector: str = Field(description="Record connector name in the registry.")
    item_pattern: str = Field(description="Item regex; group 1 or the full match is the item.")
    reason_codes_doc: str = Field(description="Reason-code document relative to the template.")
    prompt_hints: str = Field(description="Organization-specific tone and reply instructions.")
    action_item_fields: list[str] = Field(description="Fields required in action items.")
    reviewers: list[str] = Field(description="Human roles allowed to review outputs.")

    model_config = {"json_schema_extra": {"example": {
        "id": "payments", "organization": "Cedar Payment Systems",
        "languages": ["en", "ar"],
        "labels": {"unit": "Product module", "units": "Product modules",
                   "stakeholder": "Client bank", "stakeholders": "Client banks",
                   "person": "Client bank", "record": "Transaction record",
                   "item": "Payment reference", "change": "Central bank circular",
                   "request": "Bank support ticket", "reviewer": "Business analyst"},
        "connector": "transaction_lookup",
        "item_pattern": r"(?i)(?:payment|ref|transfer)\s*[#=]?\s*(\d{4,6})",
        "reason_codes_doc": "documents/reason_codes.md",
        "prompt_hints": "Sign replies as Support Team, Cedar Payment Systems.",
        "action_item_fields": ["title", "description", "unit_id", "owner_role", "due_before", "checks"],
        "reviewers": ["Business analyst", "Support engineer"],
    }}}


class Unit(BaseModel):
    """One organizational unit that a change can affect."""

    unit_id: str = Field(description="Stable identifier within the template.")
    name: str = Field(description="Human-readable unit name.")
    type: str = Field(description="Template-defined kind, such as module or program.")
    description: str = Field(description="Responsibilities and capabilities of the unit.")

    model_config = {"json_schema_extra": {"example": {
        "unit_id": "ACH", "name": "Automated Clearing House", "type": "module",
        "description": "Batch credit transfers using pacs.008, pacs.002 and pacs.004.",
    }}}


class Stakeholder(BaseModel):
    """A group associated with units and filterable attributes."""

    stakeholder_id: str = Field(description="Stable stakeholder group identifier.")
    name: str = Field(description="Fictional stakeholder group's display name.")
    type: str = Field(description="Template-defined group type used by scope matching.")
    units: list[str] = Field(description="Identifiers of units this group uses.")
    attributes: dict[str, object] = Field(description="Scope attributes and local configuration.")

    model_config = {"json_schema_extra": {"example": {
        "stakeholder_id": "BANK-C", "name": "Eastgate Bank", "type": "commercial",
        "units": ["ACH", "CHQ"], "attributes": {
            "country": "Country Y", "message_standard": "pacs.008.001.08",
            "cutoff_time": "15:00", "local_rules": ["Reject closed creditor accounts with AC04."],
        },
    }}}


class ChangeDocument(BaseModel):
    """An incoming rule, including its parsed header and full source text."""

    change_id: str = Field(description="Stable change document identifier.")
    template_id: str = Field(description="Template that owns the document.")
    title: str = Field(description="Change document title.")
    issuer: str = Field(description="Fictional authority issuing the change.")
    scope: str = Field(description="all, group type, true attribute, or key=value.")
    published: date = Field(description="Publication date.")
    effective: date | None = Field(description="Effective date, or null if unspecified.")
    text: str = Field(description="Full original text, including the header for citations.")

    model_config = {"json_schema_extra": {"example": {
        "change_id": "CHG-P-002", "template_id": "payments",
        "title": "Mandatory structured creditor address in credit transfers",
        "issuer": "Central Bank of Country X", "scope": "country=Country X",
        "published": "2026-02-10", "effective": "2026-06-01",
        "text": "MOCK DATA – fictional, for a student prototype\n1. Missing structured creditor address must be rejected with BE04.",
    }}}


class Record(BaseModel):
    """A read-only event; a null reason code denotes a successful outcome."""

    record_id: str = Field(description="Unique record identifier within the template.")
    template_id: str = Field(description="Template that owns this record.")
    timestamp: datetime = Field(description="Time the event was recorded.")
    person_id: str = Field(description="Identifier of the person or group concerned.")
    unit_id: str = Field(description="Identifier of the associated unit.")
    item: str = Field(description="Item reference, preserved as a string.")
    status: str = Field(description="Template-defined event outcome.")
    reason_code: str | None = Field(description="Failure reason; null means success.")
    detail: str = Field(description="Evidence describing the outcome; may contain fictional masking fixtures.")

    model_config = {"json_schema_extra": {"example": {
        "record_id": "T-100457", "template_id": "payments",
        "timestamp": "2026-03-02T09:12:03", "person_id": "BANK-C", "unit_id": "ACH",
        "item": "7731", "status": "REJECTED", "reason_code": "AC04",
        "detail": "pacs.002 RJCT: creditor account closed (fictional acct 0013100030212)",
    }}}


class Request(BaseModel):
    """A support question awaiting a human-reviewed reply."""

    request_id: str = Field(description="Stable request identifier.")
    template_id: str = Field(description="Template that owns the request.")
    person_id: str = Field(description="Identifier of the requester.")
    created_at: datetime = Field(description="Time the request was received.")
    subject: str = Field(description="Short request summary.")
    body: str = Field(description="Untrusted request text, including safety-test instructions.")
    priority: str = Field(description="Template-defined request triage priority.")
    status: Literal["open", "answered"] = Field(description="Whether a reviewed reply has been approved.")
    item: str | None = Field(description="Known item, or null for extraction from the body.")

    model_config = {"json_schema_extra": {"example": {
        "request_id": "P-REQ-007", "template_id": "payments", "person_id": "BANK-C",
        "created_at": "2026-03-02T10:00:00", "subject": "Rejected transfer",
        "body": "Why was payment 7731 rejected?", "priority": "medium", "status": "open", "item": None,
    }}}

# --- Part 2: SearchResult ---

# --- Part 3: Requirement, ChangeSummary, Impact, ImpactReport, Check, ActionItem ---

# --- Part 4: Investigation, TaskStep, Task ---

# --- Part 5: ReviewDecision, AuditEvent ---
