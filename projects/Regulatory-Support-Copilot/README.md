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
| 2 | Knowledge Base and AI Foundation | Khadija Hzayen | `part2_knowledge/` |
| 3 | Change Watch Agents | Khaled Amireh | `part3_change_watch/` |
| 4 | Request Desk Agent and Orchestrator | Rawan | `part4_request_desk/` |
| 5 | Website, Safety and Evaluation | Nada Alnajjar | `part5_web/` |

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

## Choose the LLM provider and template

Edit `.env`: `ACTIVE_TEMPLATE=payments` or `university` (the website's organization switcher overrides
it per browser). `LLM_PROVIDER=fake` needs no key and is for tests; it cannot extract change
requirements. For the demo use `LLM_PROVIDER=groq`, `LLM_MODEL=openai/gpt-oss-20b` and your own
`GROQ_API_KEY` (only in `.env`, never committed). Restart the website after changing `.env`.

## Run

```
python -m part2_knowledge.knowledge_base.ingest                     # build the search index (first run downloads ~80 MB)
uvicorn part5_web.app:app --reload                                  # website at http://127.0.0.1:8000
python -m part3_change_watch.cli CHG-P-002                          # Change Watch without the website
python -m part4_request_desk.orchestrator.run --request P-REQ-007   # also --change CHG-P-002, --list
python -m part5_web.evaluation.run_eval --template all              # accuracy report → docs/evaluation-report.md
pytest                                                              # all tests
```

## Demo (full script with timings: `docs/demo-script.md`)

- **Demo A – Payments, Change Watch:** New Central bank circular → `CHG-P-002` → Analyze → watch the three steps → reviewer *Business analyst* approves one action item and edits another → Action Items → Audit Log.
- **Demo B – Payments, Request Desk:** Bank support tickets → `P-REQ-007` (BANK-C: "Why was payment 7731 rejected?") → Investigate → AC04 closed account → reviewer *Support engineer* approves the reply → ticket becomes answered.
- **Demo C – University:** switch the organization to Northfield University → Student requests → `U-REQ-007` (S-2291: "Why can't I register for SE301?") → PREREQ_MISSING → reviewer *Registrar* approves → open Setup. Same code, different template.

Safety: personal and account data are masked before every model call, nothing is saved or sent
without a human decision, and every step is in the audit log (`part5_web/safety/guidelines.md`).

## Other material

- `docs/project-overview.md` – short overview of the product
- `docs/project-proposal.pdf` – the proposal sent to the doctor
- `presentation/copilot-explainer.html` – animated explainer for class
- `presentation/copilot-explainer-ar.html` – the same explainer in Arabic (right-to-left)

Part 5 keeps this README up to date with the final demo steps.
