"""Impact Analyst: constrained unit inference, deterministic stakeholders."""
from datetime import date

from contracts.schemas import ChangeSummary, Impact, ImpactReport
from part1_templates.tools.directory import list_units, stakeholders_for_unit
from part1_templates.tools.templates import load_template
from part2_knowledge.common import llm
from part2_knowledge.knowledge_base.search import search
from part3_change_watch._support import UnitSelection, data_tag, prompt, verified_sources


def initial_severity(mandatory, effective, today=None):
    today = today or date.today()
    if not mandatory:
        return "low", "Optional recommendation."
    if effective is None:
        return "medium", "Mandatory; effective date unknown, confirm deadline."
    days = (effective - today).days
    if days <= 0:
        return "high", "Mandatory and already effective or overdue."
    if days <= 90:
        return "high", "Mandatory and effective within 90 days."
    return "medium", "Mandatory and effective later than 90 days."


def analyze(summary: ChangeSummary) -> ImpactReport:
    """Infer units using actual candidates and citations; never infer stakeholders."""
    template = load_template(summary.template_id)
    units = list_units(template_id=summary.template_id)
    allowed = {unit.unit_id for unit in units}
    impacts, unmatched = [], []
    for requirement in summary.requirements:
        sources = verified_sources(search(requirement.description, k=5, filters={"doc_type": "document"},
                                          template_id=summary.template_id), summary.template_id, "document")
        selection = llm.complete_json(prompt("impact", template), data_tag("document", {
            "requirement": requirement.model_dump(mode="json"),
            "change_context": {"title": summary.title, "summary": summary.summary_text,
                               "requirements": [r.model_dump(mode="json") for r in summary.requirements]},
            "units": [unit.model_dump(mode="json") for unit in units],
            "passages": [source.model_dump(mode="json") for source in sources],
        }), UnitSelection)
        matched = set()
        for choice in selection.units:
            if choice.unit_id not in allowed or choice.unit_id in matched:
                continue
            matched.add(choice.unit_id)
            evidence = [source for i, source in enumerate(sources) if i in choice.evidence_indices
                        and source.metadata.get("unit_id") in {None, choice.unit_id}]
            severity, rule = initial_severity(requirement.mandatory, summary.effective_date)
            if choice.raise_severity and choice.escalation_reason.strip():
                severity = {"low": "medium", "medium": "high", "high": "high"}[severity]
                rule += f" Escalation rationale: {choice.escalation_reason.strip()}"
            if not evidence:
                severity = "low"
                rule += " No supporting documentation found; evidence gap requires review."
            stakeholders = sorted({group.stakeholder_id for group in stakeholders_for_unit(
                choice.unit_id, scope=summary.scope, template_id=summary.template_id)})
            impacts.append(Impact(requirement_id=requirement.requirement_id, unit_id=choice.unit_id,
                                  stakeholders=stakeholders, severity=severity,
                                  reason=f"{choice.reason.strip()} {rule}", sources=evidence))
        if not matched:
            unmatched.append(requirement.requirement_id)
    return ImpactReport(change_id=summary.change_id,
                        impacts=sorted(impacts, key=lambda i: (i.requirement_id, i.unit_id)),
                        unmatched_requirements=sorted(set(unmatched)))
