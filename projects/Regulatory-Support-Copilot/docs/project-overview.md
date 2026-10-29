# Regulatory & Support Copilot – Product Overview

A general product that any organization can customize: AI agents watch new rules and answer requests,
and a person approves every result. This overview is the short version; the full details are in
`docs/00-Project-Guide.pdf` and the five part guides.

> All data in this project is fictional mock data. The idea started as a copilot for a payments software
> company; on our doctor's advice we turned it into a product any organization can adopt.

## 1. The problem

Every organization faces the same two problems:

1. **New rules keep arriving.** A university gets a new accreditation rule, a hospital a new health
   ministry rule, a company a new law or contract. Someone must read it, find what it affects and plan the
   work. This takes days and depends on a few experts.
2. **Requests keep arriving.** Students, patients or customers ask "why did this fail?" Someone must dig
   through records to find the reason and reply. Replies are slow and staff time is wasted.

## 2. The product

One core engine with AI agents, customized for each organization by a **template**.

- The **code is the same** for every organization.
- The **template** gives the organization's name, its words (labels), its units and stakeholder groups,
  its documents, its records connector, and hints for the AI's tone.
- A **person approves** everything the agents prepare.

| | University template | Hospital template |
| --- | --- | --- |
| Organization | Northfield University | Riverside General Hospital |
| Unit | Study program / office | Department |
| Stakeholder | Student group | Patient or staff group |
| Record | Registration record | Appointment record |
| Item | Course (SE301) | Appointment (APT-5521) |
| Rule source | Higher Education Accreditation Commission | Ministry of Health of Country X |
| Reviewer | Registrar / Dean's office | Patient Services / Quality office |

Other organizations (a bank, a telecom, an online store) would only need a new template.

## 3. The two workflows and their agents

**Change Watch (Workflow A)** – a new rule arrives:

1. **Change Watcher** – summarizes the document and lists each requirement with its exact quote.
2. **Impact Analyst** – finds the affected units (search + AI) and stakeholder groups (by code, never guessed).
3. **Action Planner** – drafts action items with owner, due date and checks.
4. **Human review** – approve, edit or reject each action item.

**Request Desk (Workflow B)** – a person asks a question:

1. **Request Investigator** – finds the item in the request (template regex), looks up the person's records
   through the template's connector, reads the reason code, searches the documents for the explanation,
   and drafts a reply in the organization's tone.
2. **Human review** – approve or edit the reply before it is "sent".

## 4. Architecture in brief

- **Website** (FastAPI): pages, template switcher, Setup page, review buttons, audit log, evaluation.
- **Orchestrator**: runs each task in the background and records every step.
- **Agents**: plain Python functions; prompts are filled with the template's labels.
- **Knowledge base**: Chroma vector search, one collection per template (RAG).
- **LLM wrapper**: one place to call the model (fake, Ollama, Anthropic or OpenAI), masking personal data first.
- **Templates, connectors, tools**: read-only access to each organization's mock data.
- **Storage**: SQLite for tasks, reviews and the audit log.

## 5. Safety

- Nothing is sent or saved without a human decision.
- Connectors and tools are read-only.
- National IDs, phone numbers, emails and medical record numbers are masked before any AI call.
- Every agent step and human decision is written to an audit log.
- Text from documents and requests is treated as data, never as instructions (tested with a
  prompt-injection request in each template).

## 6. The demo

The final presentation is a live demo of the website:

- **Demo A – University, Change Watch:** circular CHG-U-001 (internship 6 → 8 weeks) → summary, impact on
  CS-BSc and SE-BSc, draft action items → approval.
- **Demo B – University, Request Desk:** U-REQ-007 from student S-2291 ("Why can't I register for SE301?")
  → PREREQ_MISSING (SE201) → reply signed by the Registrar's Office.
- **Demo C – Hospital:** switch the template → H-REQ-004 from patient P-1043 ("Why was my cardiology
  appointment on 3 March cancelled?") → DOCTOR_UNAVAILABLE → reply signed by Patient Services → Setup page.

## 7. Team parts

| Part | Folder | Responsibility |
| --- | --- | --- |
| 1 Templates, Mock Data and Connectors (Zain Allateef) | `part1_templates/` | Both templates and all mock data, record connectors, read-only tools, answer sets |
| 2 Knowledge Base and AI Foundation | `part2_knowledge/` | Ingestion and search per template, LLM wrapper, settings, prompt rendering |
| 3 Change Watch Agents | `part3_change_watch/` | Change Watcher, Impact Analyst, Action Planner |
| 4 Request Desk Agent and Orchestrator | `part4_request_desk/` | Request Investigator, task runner and task store |
| 5 Website, Safety and Evaluation | `part5_web/` | Website, template switcher, Setup page, masking, audit, evaluation |

## 8. Technology

Python 3.11, Pydantic v2, FastAPI with Jinja2, SQLite, Chroma, PyYAML, pytest, and an LLM through one
wrapper (free `fake` and `ollama` options for development). Collaboration on GitHub with one branch per
task, pull requests, and reviews.
