# Regulatory & Support Copilot

A student prototype for the AI Topics Course: a team of AI agents that helps a payments software
company handle new central bank regulations and bank support tickets, with a website where a
person reviews every result. Case study: ProgressSoft (Amman, Jordan). **All data is mock data.**

## Start here

1. Read `docs/00-Project-Guide.pdf` (whole project, rules, GitHub workflow).
2. Read your part guide in `docs/` (01 to 05).
3. Set up your environment (Project Guide, Section 10).

## Team

| Part | Title | Owner | Folders |
| --- | --- | --- | --- |
| 1 | Mock Data and Tools | | `part1_data/` |
| 2 | Knowledge Base and AI Foundation | | `part2_knowledge/` |
| 3 | Regulation Agents | | `part3_regulation/` |
| 4 | Support Agent and Orchestrator | | `part4_support/` |
| 5 | Website, Safety and Evaluation | | `part5_web/` |

Each part has **one folder**, edited only by its owner. Shared: `contracts/` (data models, all approve
changes) and `tests/integration/` (Parts 4 and 5).

## Setup

```
git clone <this repository URL>
cd AI-Topics-Course-Project/projects/ProgressSoft-Regulatory-Copilot   # run every command from this folder
python -m venv .venv
.venv\Scripts\activate              # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env               # macOS/Linux: cp .env.example .env
```

## Run (once the parts are built)

```
python -m part2_knowledge.knowledge_base.ingest   # build the search index
uvicorn part5_web.app:app --reload                # website at http://127.0.0.1:8000
pytest                                            # all tests
python -m part5_web.evaluation.run_eval           # accuracy report
```

## Other material

- `docs/project-overview.md` – the first full project description
- `docs/project-proposal.pdf` – the proposal sent to the doctor
- `presentation/copilot-explainer.html` – animated explainer for class

Part 5 keeps this README up to date with the final demo steps.
