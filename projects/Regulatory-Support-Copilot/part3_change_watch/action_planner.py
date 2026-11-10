"""Action Planner: one review-only draft per valid affected unit."""
from collections import defaultdict

from contracts.schemas import ActionItem, ChangeSummary, Check, ImpactReport
from part1_templates.tools.directory import list_units, stakeholders_for_unit
from part1_templates.tools.templates import load_template
from part2_knowledge.common import llm
from part2_knowledge.knowledge_base.search import search
from part3_change_watch._support import DraftAction, data_tag, merge_sources, prompt, verified_sources


def _meaningful(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value) and all(_meaningful(v) for v in value)
    return True


def plan(summary: ChangeSummary, report: ImpactReport) -> list[ActionItem]:
    """Return drafts only; no runtime storage, approval or send calls."""
    if report.change_id != summary.change_id:
        raise ValueError("Impact report belongs to a different change.")
    template = load_template(summary.template_id)
    units = {unit.unit_id: unit for unit in list_units(template_id=summary.template_id)}
    requirements = {r.requirement_id: r for r in summary.requirements}
    grouped = defaultdict(list)
    for impact in report.impacts:
        if impact.unit_id not in units or impact.requirement_id not in requirements:
            raise ValueError("Impact contains a foreign unit or unknown requirement.")
        verified_sources(impact.sources, summary.template_id, "document")
        expected = sorted({g.stakeholder_id for g in stakeholders_for_unit(
            impact.unit_id, scope=summary.scope, template_id=summary.template_id)})
        if sorted(set(impact.stakeholders)) != expected:
            raise ValueError("Impact stakeholders disagree with the scoped directory.")
        grouped[impact.unit_id].append(impact)
    actions = []
    for unit_id, impacts in sorted(grouped.items()):
        ids = sorted({i.requirement_id for i in impacts})
        history = verified_sources(search(" ".join([unit_id] + [requirements[i].description for i in ids]),
                                          k=2, filters={"doc_type": "past_action_item"},
                                          template_id=summary.template_id), summary.template_id, "past_action_item")
        draft = llm.complete_json(prompt("action_planner", template), data_tag("document", {
            "unit": units[unit_id].model_dump(mode="json"),
            "requirements": [requirements[i].model_dump(mode="json") for i in ids],
            "impacts": [i.model_dump(mode="json", exclude={"sources"}) for i in impacts],
            "sources": [s.model_dump(mode="json") for s in merge_sources(s for i in impacts for s in i.sources)],
            "style_only": [source.model_dump(mode="json") for source in history],
        }), DraftAction)
        if any(identifier not in draft.description for identifier in ids):
            raise ValueError("Draft description must cite every covered requirement ID.")
        if not all(_meaningful(v) for v in [draft.title, draft.description, draft.owner_role]):
            raise ValueError("Draft narrative fields must not be blank.")
        if any(not _meaningful(check.steps) or not _meaningful(check.expected) for check in draft.checks):
            raise ValueError("Draft checks need nonblank steps and expected outcomes.")
        action_id = f"AI-{summary.change_id}-{unit_id}"
        action = ActionItem(action_id=action_id, change_id=summary.change_id, title=draft.title.strip(),
                            description=draft.description.strip(), unit_id=unit_id,
                            stakeholders=sorted({s for i in impacts for s in i.stakeholders}),
                            owner_role=draft.owner_role.strip(), due_before=summary.effective_date,
                            checks=[Check(check_id=f"{action_id}-C{n}", steps=c.steps, expected=c.expected)
                                    for n, c in enumerate(draft.checks, 1)],
                            sources=merge_sources(s for i in impacts for s in i.sources), status="pending_review")
        for field in template.action_item_fields:
            if not hasattr(action, field) or not _meaningful(getattr(action, field)):
                raise ValueError(f"Required action field '{field}' cannot be filled from source; human input required.")
        actions.append(action)
    return actions
