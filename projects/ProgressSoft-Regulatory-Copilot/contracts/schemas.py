"""Shared data contracts for the Regulatory & Support Copilot.

Every model needs Field(description=...) on each field and one realistic example in
model_config = {"json_schema_extra": {"example": {...}}}.
Written on Contract Day (end of week 1); after that, changes need approval from all members.
See docs/00-Project-Guide.pdf, Section 8.
"""
from pydantic import BaseModel, Field  # noqa: F401

# --- Part 1: RegulationDoc, Client, LogEntry, Ticket ---

# --- Part 2: SearchResult ---

# --- Part 3: Change, RegulationSummary, Impact, ImpactReport, TestCase, ChangeRequest ---

# --- Part 4: TriageResult, TaskStep, Task ---

# --- Part 5: ReviewDecision, AuditEvent ---
