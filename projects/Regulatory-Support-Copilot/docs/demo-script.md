# Demo script (about 10 minutes + questions)

**Before class:** `.env` uses the demo model (`LLM_PROVIDER=groq`, `LLM_MODEL=openai/gpt-oss-20b`,
your local `GROQ_API_KEY`). Run `python -m part2_knowledge.knowledge_base.ingest`, then start
`uvicorn part5_web.app:app` and open http://127.0.0.1:8000. Run Demo A once before class so you know
it works, and keep the backup video ready.

| Time | Who | What to do | What to say |
| --- | --- | --- | --- |
| 0:00–1:00 | Opening | Open `presentation/copilot-explainer.html` | Every organization gets new rules and support questions. Our product: AI agents do the reading and drafting; a person approves. One engine, customized by a template. |
| 1:00–4:00 | **Demo A** – Payments, Change Watch | Organization = Cedar Payment Systems → **Central bank circulars** → `CHG-P-002` row → **Analyze**. Watch the three steps run. | The quote boxes are word for word from the circular. Affected product modules ACH and IPS; client banks BANK-A, BANK-B, BANK-E. Every claim has its source. |
| | | Reviewer = **Business analyst** → **Approve** one action item, **Edit** another (change the description) → Save. Open **Action Items**, then **Audit Log**. | Nothing reaches the action list without a human click. Every step and decision is in the audit log. |
| 4:00–6:00 | **Demo B** – Payments, Request Desk | **Bank support tickets** → `P-REQ-007` (BANK-C: "Why was payment 7731 rejected?") → **Investigate**. | The transaction record shows AC04, closed account. The reply is a draft – it has not been sent. |
| | | Reviewer = **Support engineer** → **Approve**. Back to the ticket list: status *answered*. | Account numbers in the records are masked before the model sees them. |
| 6:00–9:00 | **Demo C** – switch to University | Organization = **Northfield University**. Point at the header and menu: Student requests, Study programs. **Student requests** → `U-REQ-007` (S-2291: "Why can't I register for SE301?") → **Investigate**. | Same code, different template. PREREQ_MISSING: SE201 is missing. |
| | | Reviewer = **Registrar** → **Approve**. Open **Setup**. | Only this folder changed: labels, units, stakeholder groups, connector, item pattern. A new organization is a new folder, not new code. |
| 9:00–10:00 | Closing | Open **Evaluation**. | One table per template: search hit@5, Change Watch and Request Desk accuracy, 0 masking leaks. Safety story: masking, human approval, audit log, prompt-injection tests. |

**If something fails:** a failed step shows its error and a **Retry** button – that is part of the
story. If the network or model is down, switch to the backup video and continue talking.

**Rehearsals:** two full runs in week 8, timed. Record the backup video on the second run.

| Rehearsal | Date | Time taken | Problems |
| --- | --- | --- | --- |
| 1 | | | |
| 2 | | | |
