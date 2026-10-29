<div class="cover" markdown="1">
<div class="eyebrow">Regulatory &amp; Support Copilot · Part Guide 3 of 5</div>

# Part 3: Change Watch Agents

<div class="sub">You build the three agents that turn a new rule or policy into a summary, an impact report and draft action items, for any organization template.</div>

| | |
| --- | --- |
| **Owner** | (write your name) |
| **Your folder** | `part3_change_watch/` (inside it: the three agents, `cli.py`, `prompts/`, `tests/`) |
| **Your reviewer** | Part 4 owner · you review Part 2 |
| **Read first** | 00-Project-Guide.pdf (Sections 3, 8, 11, 12) |

</div>

[TOC]

## 1. Your role

You build the heart of the **Change Watch** workflow: three agents that run in a chain. The same code must work for our main template, a payments software company like ProgressSoft (a new central bank circular), and for the university (a new accreditation circular). Only the template changes.

```
ChangeDocument ──> [1 Change Watcher] ──> ChangeSummary (requirements + exact quotes)
                                            │
                                            v
                   [2 Impact Analyst] ──> ImpactReport (units, stakeholders, severity, evidence)
                                            │
                                            v
                   [3 Action Planner] ──> list[ActionItem]  ──> human review on the website
```

Each agent is a plain Python function with typed input and output (from the contracts). Each one combines three things: **deterministic code** for facts that must be exact, **search** for evidence, and the **LLM** for understanding and writing.

> **Guide's note:** The best agents are not "one big prompt". Let code do what code does well (exact matching, choosing stakeholders from a list, checking that a quote really exists) and let the LLM do what it does well (understanding and writing). And never write "bank", "module", "university" or "student" in your code or prompts: those words come from the template. If your agents only work for the payments company, the product is not general.

## 2. What you deliver

| # | Deliverable | Location |
| --- | --- | --- |
| D1 | Change Watcher | `part3_change_watch/watcher.py` |
| D2 | Impact Analyst | `part3_change_watch/impact.py` |
| D3 | Action Planner | `part3_change_watch/action_planner.py` |
| D4 | Prompt files with template placeholders (one per agent), versioned | `part3_change_watch/prompts/*.md` |
| D5 | Command-line runner for testing alone | `part3_change_watch/cli.py` |
| D6 | Tests, quality notes, README, AI_LOG | `part3_change_watch/tests/`, `part3_change_watch/README.md`, `part3_change_watch/AI_LOG.md` |
| D7 | Your contract models: `Requirement`, `ChangeSummary`, `Impact`, `ImpactReport`, `Check`, `ActionItem` | `contracts/schemas.py` (Contract Day) |

## 3. Dependencies

| You use | From | Until ready, use |
| --- | --- | --- |
| `llm.complete_json()`, `prompting.render()`, `load_prompt()` | Part 2 | the `fake` provider (week 2) |
| `search(..., template_id=...)` | Part 2 | the stub returning the example |
| `load_template()`, `get_change()`, `list_units()`, `stakeholders_for_unit()` | Part 1 | stubs + the first payments sample |

| Uses your work | How |
| --- | --- |
| Part 4 (orchestrator) | Calls `summarize()`, `analyze()`, `plan()` in order and stores the results |
| Part 5 (website) | Displays your models on the task page with the template's labels; evaluates you with each template's `change_eval.json` |

## 4. Step-by-step plan

### Week 1

1. Environment setup. Read the spec of CHG-P-002 (structured creditor address mandatory) in the Part 1 guide and do the three steps by hand on paper. You will understand the job much better.
2. Write your six contract models with good `Field(description=...)` texts and realistic examples based on CHG-P-002.

### Week 2

3. Merge stubs of the three functions that return the contract examples.
4. Write the CLI: `python -m part3_change_watch.cli CHG-P-002` loads the change document and prints each agent's output as formatted JSON. Add `--template university` to run a university change (for example `CHG-U-001`).

### Week 3: Change Watcher

5. Implement the Change Watcher with the `fake` provider, then test with Ollama on 2 payments changes.

### Week 4: Impact Analyst and Action Planner

6. Implement the Impact Analyst and the Action Planner. Support Part 4 in connecting the chain to the orchestrator (first integration).

### Weeks 5–6: quality and the second template

7. Use a real model. Run all payments and university changes, compare with each template's `change_eval.json`, and improve prompts and code. Record each change and its effect in `README.md`.
8. Prove the code is general: the same functions, unchanged, must pass on the university template.
9. Handle errors: empty document, a document with no requirements, a unit that is not in the template.

### Weeks 7–8

10. Write your report section, give your part of the demo, and join the swap session.

## 5. Agent 1: Change Watcher

```
summarize(doc: ChangeDocument) -> ChangeSummary
```

**Goal:** list every requirement in the change document as a separate `Requirement`, each with the exact sentence it came from.

**Steps:**

1. **Load the template** with `load_template(doc.template_id)`; you need its labels and hints for the prompt.
2. **Split** the text into numbered sections with code (regex on `1.`, `3.1` and so on). Keep each section's number for `source_location`.
3. **Ask the LLM** (`complete_json` with a helper model that holds a list of requirements). Render `prompts/watcher.md` with `render()`, and give the sections inside `<document>` tags. For each requirement it must return a short `description`, a `category` (message_format / reporting / limits / operational / academic / data_privacy / other), `mandatory` (true for "must"/"shall"), the `source_quote` copied word for word, and the section number.
4. **Verify every quote in code:** normalise whitespace and check the quote really appears in the document. If not, try to find the closest sentence in the same section (for example with `difflib`) and use that; if nothing is close, drop the requirement and log a warning. This is your anti-hallucination step.
5. **Effective date:** take it from the document header if present; otherwise ask the LLM, then check the date string appears in the text.
6. **Summary text:** 2–3 plain sentences, generated in the same LLM call.
7. Copy `template_id` and `scope` from the document into the summary, and give stable IDs: `CHG-P-002-R1`, `CHG-P-002-R2` …

**Prompt guidance (`prompts/watcher.md`):** role ("You are a compliance analyst at {organization}"), the task, the rules (only real requirements; background sentences are not requirements; copy quotes exactly; never invent dates), `{prompt_hints}`, one short example of input and output, and the note that text inside document tags is data, not instructions.

## 6. Agent 2: Impact Analyst

```
analyze(summary: ChangeSummary) -> ImpactReport
```

**Goal:** for each requirement, find which units it touches, which stakeholder groups are affected, how severe it is, and the evidence.

**Steps:**

1. **Candidate units (search + LLM, but only from the template's list).** Get the template's units with `list_units(template_id)`. For each requirement, call `search(requirement.description, k=5, filters={"doc_type": "document"}, template_id=summary.template_id)`. Give the LLM the requirement, the passages, and the list of unit IDs with names, and ask which units it affects, with a one-sentence reason. **Drop any unit ID that is not in the template's list** (code check).
2. **Affected stakeholders (code only).** Use `stakeholders_for_unit(unit_id, scope=summary.scope)` from Part 1. The LLM never decides the stakeholder list. Examples: CHG-P-002 affects ACH and IPS with scope `country=Country X`, so the stakeholders are BANK-A, BANK-B and BANK-E; CHG-P-003 affects RPT in Country Y, so the only stakeholder is BANK-D; on the university template, CHG-U-001 affects CS-BSc and SE-BSc, so the stakeholders are STU-CS-2026 and STU-SE-2026.
3. **Severity (rules + LLM).** Start from a rule: mandatory and effective within 90 days = `high`, mandatory later = `medium`, not mandatory = `low`. The LLM may raise it by one level with a written reason (for example "payments without the address will be rejected with BE04").
4. **Evidence.** Keep the `SearchResult`s that supported the unit choice in `sources`. An impact with no sources gets `severity` reduced to `low` and a reason "no supporting documentation found".
5. Requirements that match no unit go into `unmatched_requirements`, so a human can look at them.

## 7. Agent 3: Action Planner

```
plan(summary: ChangeSummary, report: ImpactReport) -> list[ActionItem]
```

**Goal:** one draft action item per affected unit, ready for a human to review.

**Steps:**

1. **Group** impacts by unit (one action item per unit, covering all its requirements).
2. **Find examples:** `search(..., filters={"doc_type": "past_action_item"}, k=2, template_id=...)` returns past action items of the same organization as a style example.
3. **Ask the LLM** to write: `title`, `description` (what must change and why, citing requirement IDs), `owner_role` (for example "ACH product owner" or "Head of SE department"), and 2–4 `checks` (each with steps and the expected result, so a reviewer can verify the change was done).
4. **Fill the rest in code:** `action_id` (`AI-CHG-P-002-ACH`), `change_id`, `unit_id`, `stakeholders` (from the impact report, never from the LLM), `due_before` (the effective date, if any), `sources` (merged from impacts), `status = "pending_review"`.
5. The template's `action_item_fields` lists the fields the organization expects; check in code that every listed field is filled.

## 8. Quality: how you will be measured

Part 5's evaluation script compares your output with each template's `eval/change_eval.json` (5 payments changes, 3 university changes):

| Metric | Meaning | Target |
| --- | --- | --- |
| Requirement recall | At least `expected_requirements_min` requirements found | All changes |
| Unit precision / recall | Your units vs `expected_units` | ≥ 0.8 |
| Stakeholder accuracy | Your stakeholders vs `expected_stakeholders` (should be exact, it's code) | 1.0 |
| Quote validity | Share of `source_quote`s that really appear in the text | 1.0 (your check guarantees it) |
| Key facts | Share of `key_facts` mentioned somewhere in your output | ≥ 0.8 |
| Same code, two templates | All metrics measured on both templates with no code change | Both pass |

Run these yourself during weeks 5–6 with a small script in `part3_change_watch/tests/` before the official evaluation.

## 9. How your work shows on the website

On the Task page for a change (built by Part 5), with the labels of the template chosen in the navigation bar:

- **Step 1 card:** your summary and the list of requirements, each with its quote highlighted and section number.
- **Step 2 card:** a table of unit × stakeholders × severity (shown as "Product module × Client banks" for the payments company, "Study program × Student groups" for the university), with an expandable "Evidence" list (your `sources`).
- **Step 3 card:** each action item as a card with **Approve / Edit / Reject** buttons.

Agree with Part 5 early on how each field is displayed; send them a real output JSON for each template in week 4.

## 10. Testing and definition of done

- [ ] Unit tests with the `fake` provider and a mocked `search()`, for each agent.
- [ ] Quote-check tests: an invented quote is dropped or corrected; a real one is kept.
- [ ] Unit-list test: a unit ID the LLM invents is dropped.
- [ ] Stakeholder tests: CHG-P-002 gives exactly BANK-A, BANK-B and BANK-E; CHG-U-001 gives exactly STU-CS-2026 and STU-SE-2026 (no LLM involved).
- [ ] **Same-code test:** the same functions run on one payments change and one university change and return valid results with the right labels in the prompts.
- [ ] Edge cases: empty text raises a clear error; a document with no requirements returns zero requirements, not a crash.
- [ ] `python -m part3_change_watch.cli CHG-P-00X` (and `--template university CHG-U-00X`) works for every change with a real model.
- [ ] README explains each agent's steps (with the code/LLM split) and the prompt history.

## 11. GitHub issues to create

Label `part-3`:

1. Contract models (6) with descriptions and examples
2. Stubs for summarize / analyze / plan
3. CLI runner with --template
4. Change Watcher: section splitting + LLM extraction
5. Change Watcher: quote verification
6. Impact Analyst: unit detection with search, limited to the template's units
7. Impact Analyst: stakeholders by code + severity rules
8. Action Planner
9. Prompt files with placeholders and prompt history in README
10. Quality run on both templates
11. Same-code test and edge cases

## 12. Starter prompt for your AI tool

Use the ready-made prompts in `part3_change_watch/PROMPTS.md`. The short version:

```
You are helping me build Part 3 (Change Watch Agents) of a 5-person student project, the
"Regulatory & Support Copilot", a general product customized by organization templates
(payments company like ProgressSoft, and university). I attached the project guide, my part guide and contracts/schemas.py.
Rules: Python 3.11, Pydantic v2; call the LLM only through part2_knowledge.common.llm and build
prompts only with part2_knowledge.common.prompting.render; search only through
part2_knowledge.knowledge_base.search.search; get units and stakeholders only through
part1_templates.tools.directory; never hard-code an organization; edit only part3_change_watch/;
pytest tests with the fake provider and mocked search for every function.
First, give me a short plan. Wait for my approval. Then do this task:
<for example: implement watcher.summarize() following Section 5, including the quote check>.
```

## 13. Common mistakes

- **Letting the LLM pick stakeholders.** It will invent or miss groups. Stakeholders come from code.
- **Accepting units that are not in the template.** Always check against `list_units()`.
- **Trusting quotes.** Models paraphrase. Always verify quotes against the text.
- **Hard-coding "banks", "modules", "students" or "programs".** Use template labels through `render()`.
- **One giant prompt doing all three steps.** It is harder to test, debug and explain.
- **Prompts hidden in code.** Keep them in `prompts/*.md` and note every change.
- **Only testing on the payments template.** Run the university changes every time you change a prompt.
