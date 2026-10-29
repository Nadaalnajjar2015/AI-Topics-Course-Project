# Regulatory & Support Copilot for ProgressSoft

An agentic AI system that helps a payments software vendor keep up with central-bank regulation changes and resolve bank support tickets faster.

> **Note:** ProgressSoft is a real Jordanian fintech company. The problem described here is inferred from the nature of its business (payment and clearing systems for central and commercial banks). It is not based on internal company data. Treat it as a realistic case study and validate assumptions before building a real product.

---

## 1. Company Background

- **Company:** ProgressSoft Corporation, headquartered in Amman, Jordan.
- **Domain:** Financial technology: payment and clearing infrastructure.
- **Products (examples):** Cheque truncation and clearing systems, Automated Clearing House (ACH), instant payment systems, mobile wallets, and related banking solutions.
- **Clients:** Central banks and commercial banks across the Middle East, Africa, and Asia.

Every client country has its own regulations, message formats, and audit requirements, so one core product runs in many different configurations.

---

## 2. Problem Statement

ProgressSoft-style vendors face two connected, time-consuming problems:

1. **Regulatory change management.** Central banks regularly publish new circulars, rule updates, and message format changes (for example, ISO 20022 field updates, AML/CFT requirements, reporting formats). Each change must be read, understood, mapped to the product, and turned into development work for every affected client.
2. **Repetitive technical support.** Banks submit tickets such as *"Why was this cheque/payment rejected?"* Answering requires an engineer to read transaction logs, rejection codes, and client-specific configurations.

---

## 3. Causes of the Problem

| Cause | Effect |
|-------|--------|
| One product with many client-specific configurations | Hard to know which clients a regulation change affects |
| Frequent, long regulatory documents (often PDF, sometimes Arabic/French/English) | Business analysts spend days reading and summarizing |
| Manual mapping from regulation to product modules | Slow, error-prone, depends on few senior experts |
| Knowledge scattered across docs, tickets, and people's heads | Same questions are answered again and again |
| Support tickets need log analysis by engineers | Long resolution times and engineers pulled away from development |

---

## 4. Project Goals

- Reduce the time from *"new regulation published"* to *"approved change request"*.
- Automatically identify which modules, fields, and clients are affected by a change.
- Draft high-quality change requests with acceptance criteria and test cases.
- Resolve or pre-diagnose common support tickets automatically.
- Keep humans in control of every decision that affects production or clients.

### Out of Scope

- The system **does not** modify production code or client configurations by itself.
- The system **does not** send replies to banks without human approval.
- The system **does not** process live payment transactions.

---

## 5. Users (Personas)

| User | Needs |
|------|-------|
| **Business Analyst** | Fast summaries of new regulations and their impact |
| **Product Manager** | Prioritized list of required changes per client |
| **Support Engineer** | Root-cause diagnosis of tickets and drafted replies |
| **QA Engineer** | Generated test cases linked to each change |
| **Compliance Officer** | Audit trail of how each regulation was handled |

---

## 6. Proposed Solution

A **multi-agent system** coordinated by a supervisor (orchestrator) agent. Each specialist agent has one clear responsibility.

### 6.1 Agents

#### Orchestrator (Supervisor) Agent
- Receives incoming tasks (new regulation document or new support ticket).
- Decides which specialist agents to call and in what order.
- Collects results and sends them to the human reviewer.

#### Regulation Watcher Agent
- Monitors sources: central bank websites, uploaded circulars, standards updates.
- Extracts the document text (including scanned PDFs via OCR).
- Produces a structured summary: what changed, effective date, mandatory vs. optional items.

#### Impact Analysis Agent
- Compares the regulation summary with the product documentation and each client's configuration.
- Outputs an impact report: affected modules, message fields, reports, and clients.
- Assigns a severity/priority level to each impact.

#### Change Request Agent
- Turns the impact report into structured change requests.
- Each request includes: description, affected components, acceptance criteria, and suggested test cases.
- Pushes drafts to the ticketing system (e.g., Jira) in a "Pending Review" state.

#### Support Triage Agent
- Reads incoming bank support tickets.
- Queries transaction logs and rejection codes (read-only access).
- Explains the root cause in plain language.
- Either drafts a reply for the support engineer or escalates with a full diagnosis attached.

### 6.2 High-Level Architecture

```
                    +---------------------------+
                    |    Human Review Portal    |
                    | (approve / edit / reject) |
                    +-------------+-------------+
                                  ^
                                  |
                    +-------------+-------------+
   Regulation  ---> |    Orchestrator Agent     | <--- Support Tickets
   Documents        +--+------+-------+------+--+
                       |      |       |      |
          +------------+  +---+---+ +-+------+---+  +----------------+
          | Regulation |  | Impact| |  Change    |  | Support Triage |
          |  Watcher   |  |Analysis| |  Request  |  |     Agent      |
          +-----+------+  +---+---+ +-----+------+  +-------+--------+
                |             |           |                 |
        +-------+-------------+-----------+-----------------+------+
        |                     Tools & Data Layer                    |
        | Vector DB (docs, schemas, configs) | Log Query API (R/O)  |
        | ISO 20022 Validator | Ticketing API | Audit Log Store      |
        +-----------------------------------------------------------+
```

### 6.3 Main Workflows

**Workflow A: New Regulation**
1. A new circular is uploaded or detected.
2. The Regulation Watcher extracts and summarizes it.
3. The Impact Analysis agent identifies affected modules and clients.
4. The Change Request agent drafts change requests and test cases.
5. A Business Analyst reviews, edits, and approves.
6. Approved requests are created in the ticketing system.

**Workflow B: Support Ticket**
1. A bank opens a ticket.
2. The Support Triage agent reads it and queries the related logs.
3. The agent identifies the rejection reason and the matching rule/config.
4. A drafted reply plus diagnosis goes to the support engineer.
5. The engineer approves or edits the reply before sending.

---

## 7. Data Sources

| Data | Purpose |
|------|---------|
| Product documentation and user manuals | Understanding modules and features |
| ISO 20022 and local message schemas | Validating field-level impacts |
| Per-client configuration files | Knowing which clients are affected |
| Historical change requests | Examples for drafting new requests |
| Historical support tickets and resolutions | Learning common issues and answers |
| Transaction logs and rejection codes | Diagnosing support tickets |
| Regulatory circulars | Input for change detection |

---

## 8. Technical Explanation

### 8.1 Core Components

- **LLM layer:** A strong reasoning model for the orchestrator and analysis agents. A smaller, cheaper model can handle simple extraction tasks.
- **RAG (Retrieval-Augmented Generation):** All documents are split into chunks, converted to embeddings, and stored in a vector database. Agents retrieve relevant chunks before answering, which keeps answers grounded in real company documents.
- **Tool calling:** Agents call external tools through defined APIs: log search, schema validator, ticketing system, document parser.
- **Shared state / memory:** Each task has a shared state object (e.g., regulation summary, impact list, draft requests) passed between agents.
- **Audit log:** Every agent action, input, output, and human decision is recorded for compliance.

### 8.2 Suggested Technology Stack (students may choose alternatives)

| Layer | Options |
|-------|---------|
| Agent framework | LangGraph, CrewAI, AutoGen, or Claude Agent SDK |
| LLM | Claude, GPT, or an open-source model (Llama, Qwen) for on-premise |
| Vector database | Qdrant, Weaviate, pgvector, Chroma |
| Document parsing | OCR engine + PDF/layout parser |
| Backend | Python (FastAPI) or Node.js |
| Frontend (review portal) | React or a simple web dashboard |
| Ticketing integration | Jira API (or a mock ticketing service) |
| Storage | PostgreSQL for metadata and audit logs |

### 8.3 Security & Guardrails

- **Human-in-the-loop:** No change request or client reply is final without human approval.
- **Read-only access** to logs and configurations.
- **Data residency:** Banking data must stay on-premise or in an approved private cloud. Prefer self-hosted models when data cannot leave the network.
- **PII masking:** Account numbers and personal data are masked before being sent to any LLM.
- **Role-based access:** Users only see clients and data they are authorized for.
- **Prompt-injection protection:** Treat content from uploaded documents and tickets as data, never as instructions.
- **Full audit trail** for regulators.

---

## 9. Evaluation Metrics

| Metric | Target Idea |
|--------|-------------|
| Time from regulation release to approved change request | Reduce significantly (e.g., days to hours) |
| Impact analysis accuracy (compared to expert review) | High precision and recall on affected modules/clients |
| Change request acceptance rate (approved with few edits) | Increasing over time |
| Ticket first-response time | Reduced |
| Percentage of tickets correctly pre-diagnosed | Measured against engineer's final diagnosis |
| Hallucination rate (claims not supported by sources) | As close to zero as possible |

---

## 10. Suggested Project Phases (for Students)

| Phase | Deliverable |
|-------|-------------|
| **1. Research** | Study payment systems basics, ISO 20022, and the role of central banks |
| **2. Data preparation** | Create mock product docs, client configs, sample circulars, and sample logs |
| **3. RAG knowledge base** | Index documents in a vector database and test retrieval quality |
| **4. Single agents** | Build and test each agent separately |
| **5. Orchestration** | Connect agents through the orchestrator and shared state |
| **6. Human review portal** | Simple UI for approve/edit/reject |
| **7. Guardrails & security** | PII masking, read-only tools, audit logging |
| **8. Evaluation** | Measure metrics on a test set of regulations and tickets |
| **9. Final demo & report** | End-to-end demo of both workflows |

---

## 11. Expected Deliverables

- Working prototype covering Workflow A (regulation) and Workflow B (support ticket).
- Mock dataset (documents, configs, logs, tickets).
- Architecture diagram and technical report.
- Evaluation results with metrics.
- Short presentation and live demo.

---

## 12. Risks & Challenges

| Risk | Mitigation |
|------|------------|
| LLM misreads a regulation | Cite source paragraphs; mandatory human review |
| Sensitive banking data exposure | On-premise models, masking, strict access control |
| Incomplete or outdated documentation | Flag low-confidence answers; continuous doc updates |
| Multilingual regulations (Arabic, French, English) | Use multilingual embeddings and models; test per language |
| Over-trust by users | Show confidence levels and sources in every output |

---

## 13. Key Learning Outcomes

- Designing multi-agent systems with a supervisor pattern.
- Building RAG pipelines on domain-specific documents.
- Safe tool calling with read-only and approval-gated actions.
- Applying security and compliance thinking to AI in banking.
- Evaluating agentic systems with measurable metrics.
