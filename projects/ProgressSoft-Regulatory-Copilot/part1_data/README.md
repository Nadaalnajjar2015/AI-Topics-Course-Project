# Part 1: Mock Data and Tools

**Owner:** (Zain Allateef egdfyt)
**Guide:** `docs/01-Part1-Mock-Data-and-Tools.pdf`

Fictional company world (product docs, clients, regulations, logs, tickets, history, evaluation answer sets) and the read-only tools agents use to look up facts.

```
part1_data/
data/  – all mock data (company/, clients/configs/, regulations/, logs/, tickets/, history/, eval/, generators/)
tools/ – regulations.py, log_search.py, client_config.py, iso_validator.py, ticketing.py
tests/ – tests for this part
```

Only the owner edits this folder. Other parts use it only through the public functions listed in
`docs/00-Project-Guide.pdf`, Section 8.2. Replace this file with your own one-page README
(what the part does, inputs and outputs, how to run and test it).
