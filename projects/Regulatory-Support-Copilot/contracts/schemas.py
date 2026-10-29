"""Shared data contracts for the Regulatory & Support Copilot (general version).

The code speaks in general words (template, unit, stakeholder, record, request, action item);
each organization's template.yaml gives them their labels.
Every model needs Field(description=...) on each field and one realistic example in
model_config = {"json_schema_extra": {"example": {...}}}.
Written on Contract Day (end of week 1); after that, changes need approval from all members.
See docs/00-Project-Guide.pdf, Section 8.
"""
from pydantic import BaseModel, Field  # noqa: F401

# --- Part 1: TemplateConfig, Unit, Stakeholder, ChangeDocument, Record, Request ---

# --- Part 2: SearchResult ---

# --- Part 3: Requirement, ChangeSummary, Impact, ImpactReport, Check, ActionItem ---

# --- Part 4: Investigation, TaskStep, Task ---

# --- Part 5: ReviewDecision, AuditEvent ---
