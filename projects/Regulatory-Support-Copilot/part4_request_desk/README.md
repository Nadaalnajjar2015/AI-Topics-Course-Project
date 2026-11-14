# Part 4: Request Desk Agent and Orchestrator

Part 4 investigates a support request from its template-specific records and knowledge sources, then runs Request Investigator or Change Watch workflows and saves their outputs for human review. Draft replies and action items are never sent or approved automatically.

## Request Investigator

`investigate(request) -> Investigation`:

1. Loads the request's organization template and extracts an item with its `item_pattern`; a structured LLM fallback is accepted only when its quoted text matches that same pattern.
2. Uses document search for general questions, or searches the requester's records. If no item is given, it matches named units and selects the latest failed record in those units.
3. Retrieves the configured reason-code guidance and similar past requests, then asks the shared LLM interface for a concise root cause and draft reply.
4. Sets confidence and escalation from record and source evidence. The template supplies labels, item pattern, knowledge documents, reply guidance, and exact signature.

The request, evidence, and sources are untrusted data. Replies must not disclose full account numbers or other people's personal data.

## Task lifecycle

The orchestrator stores a `Task` with its template ID, inputs, steps, and JSON outputs. Background starts return a task ID immediately; synchronous runners support evaluation. Each step moves from `waiting` to `running` and then `done` or `failed`. Errors are saved on the failed step, and `retry_task()` starts a new task using the original input. Successful workflows end in `pending_review`; a person must review the draft.

Change Watch outputs: `summary`, `impact_report`, `action_items`. Request workflow output: `investigation`.

## Templates

No organization-specific rules are hard-coded. Selecting `payments` or `university` changes item extraction, unit and record lookup, document retrieval, vocabulary, and reply signature through `template.yaml`. The same workflows are tested with both.

## Run and test

From `projects/Regulatory-Support-Copilot/`, configure `.env` and ingest the selected templates' documents before using real retrieval:

```powershell
python -m part4_request_desk.orchestrator.run --request P-REQ-007
python -m part4_request_desk.orchestrator.run --request U-REQ-007 --template university
python -m part4_request_desk.orchestrator.run --change CHG-P-002
python -m part4_request_desk.orchestrator.run --list
pytest part4_request_desk/tests tests/integration
python -m part4_request_desk.tests.quality_check --template all
```

Quality evaluation requires the team's configured real LLM provider and a populated knowledge index; the fake provider is for tests, not an accuracy score.
