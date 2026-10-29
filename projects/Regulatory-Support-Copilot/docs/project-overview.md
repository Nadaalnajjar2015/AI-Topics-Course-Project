# Regulatory & Support Copilot – Product Overview

A general product that any organization can customize: AI agents watch new rules and answer requests,
and a person approves every result. This overview is the short version; the full details are in
`docs/00-Project-Guide.pdf` and the five part guides.

> All data in this project is fictional mock data. The idea started as a copilot for payments software
> companies like ProgressSoft (Amman); on our doctor's advice we turned it into a product any organization
> can adopt. A payments software company stays the main example.

## 1. The problem

Every organization faces the same two problems:

1. **New rules keep arriving.** A payments software company gets a new central bank circular, a university
   a new accreditation rule, a company a new law or contract. Someone must read it, find what it affects and
   plan the work. This takes days and depends on a few experts.
2. **Requests keep arriving.** Client banks, students or customers ask "why did this fail?" ("Why was
   payment 7731 rejected?"). Someone must dig through records to find the reason and reply. Replies are slow
   and staff time is wasted.

## 2. The product

One core engine with AI agents, customized for each organization by a **template**.

- The **code is the same** for every organization.
- The **template** gives the organization's name, its words (labels), its units and stakeholder groups,
  its documents, its records connector, and hints for the AI's tone.
- A **person approves** everything the agents prepare.

| | Payments template (main) | University template (second) |
| --- | --- | --- |
| Organization | Cedar Payment Systems (like ProgressSoft) | Northfield University |
| Unit | Product module (CHQ, ACH, IPS, WAL, RPT) | Study program / office |
| Stakeholder | Client bank (BANK-A … BANK-E) | Student group |
| Record | Transaction record | Registration record |
| Item | Payment reference (7731) | Course (SE301) |
| Reason codes | ISO 20022 (AC04, BE04 …) | PREREQ_MISSING, SECTION_FULL … |
| Rule source | Central Bank of Country X / Y | Higher Education Accreditation Commission |
| Reviewer | Business analyst / Support engineer | Registrar / Dean's office |

Other organizations (a hospital, a telecom, an online store) would only need a new template.

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
- IBANs, account and card numbers, national IDs, phone numbers and emails are masked before any AI call.
- Every agent step and human decision is written to an audit log.
- Text from documents and requests is treated as data, never as instructions (tested with a
  prompt-injection request in each template: P-REQ-015 and U-REQ-010).

## 6. The demo

The final presentation is a live demo of the website:

- **Demo A – Payments, Change Watch:** central bank circular CHG-P-002 (structured creditor address
  mandatory, missing → BE04) → summary, impact on ACH and IPS for BANK-A, BANK-B, BANK-E → draft action
  items → approval.
- **Demo B – Payments, Request Desk:** P-REQ-007 from BANK-C ("Why was payment 7731 rejected?") → AC04
  closed account → reply signed "Support Team, Cedar Payment Systems".
- **Demo C – University:** switch the template → U-REQ-007 from student S-2291 ("Why can't I register for
  SE301?") → PREREQ_MISSING (SE201) → reply signed by the Registrar's Office → Setup page.

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
