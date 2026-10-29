# Regulatory & Support Copilot

A general product any organization can customize: AI agents watch new rules and answer requests,
and a person approves every result. Each organization is set up with a **template** (no new code);
this prototype ships two: **Payments** (main: Cedar Payment Systems, a payments software company like
ProgressSoft) and **University** (second: Northfield University). **All data is mock data.**

## Start here

1. Read `docs/00-Project-Guide.pdf` (the whole product, rules, GitHub workflow).
2. Read your part guide in `docs/` (01 to 05).
3. Set up your environment (Project Guide, Section 10).
4. Open `PROMPTS.md` in your part folder: five ready prompts for your AI coding tool. Start with Prompt 1.

## Team

| Part | Title | Owner | Folder |
| --- | --- | --- | --- |
| 1 | Templates, Mock Data and Connectors | Zain Allateef | `part1_templates/` |
| 2 | Knowledge Base and AI Foundation | | `part2_knowledge/` |
| 3 | Change Watch Agents | | `part3_change_watch/` |
| 4 | Request Desk Agent and Orchestrator | | `part4_request_desk/` |
| 5 | Website, Safety and Evaluation | | `part5_web/` |

Each part has **one folder**, edited only by its owner. Shared: `contracts/` (data models, all approve
changes) and `tests/integration/` (Parts 4 and 5).

## Setup

```
git clone https://github.com/Nadaalnajjar2015/AI-Topics-Course-Project.git
cd AI-Topics-Course-Project/projects/Regulatory-Support-Copilot   # run every command from this folder
python -m venv .venv
.venv\Scripts\activate              # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env               # macOS/Linux: cp .env.example .env
```

`ACTIVE_TEMPLATE` in `.env` chooses the organization (`payments`, the default, or `university`); the website can also switch it.

## Run (once the parts are built)

```
python -m part2_knowledge.knowledge_base.ingest                     # build the search index (all templates)
uvicorn part5_web.app:app --reload                                  # website at http://127.0.0.1:8000
python -m part3_change_watch.cli CHG-P-002                          # Change Watch without the website
python -m part4_request_desk.orchestrator.run --request P-REQ-007   # also --change CHG-P-002, --list
python -m part5_web.evaluation.run_eval --template all              # accuracy report (payments, university, all)
pytest                                                              # all tests
```

## Demo

- **Demo A – Payments, Change Watch:** New Change → `CHG-P-002` (structured creditor address mandatory, missing → BE04) → Analyze → review the action items for ACH and IPS.
- **Demo B – Payments, Request Desk:** Requests → `P-REQ-007` from BANK-C ("Why was payment 7731 rejected?") → Investigate → AC04 closed account → approve the reply.
- **Demo C – University:** switch the template → `U-REQ-007` ("Why can't I register for SE301?") → Investigate → open the Setup page. Same code, different template.

## Other material

- `docs/project-overview.md` – short overview of the product
- `docs/project-proposal.pdf` – the proposal sent to the doctor
- `presentation/copilot-explainer.html` – animated explainer for class

Part 5 keeps this README up to date with the final demo steps.
