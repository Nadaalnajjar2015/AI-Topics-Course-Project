# QA suites (black-box, against a running server)

Unit and integration tests stay in `pytest`. These suites test the **running** website the way a
user does. Run them only against the local QA server, never against production.

```powershell
python tests/qa/launch_qa_server.py          # terminal 1: isolated server on :8100 (fake model)
python tests/qa/qa_http.py                   # terminal 2: 156 HTTP checks (auth, pages, API, review
                                             #   rules, races, injection, CSRF, headers, DB triggers, load)
cd tests/qa; npm install; npx playwright install firefox webkit
npm run e2e                                  # Edge/Firefox/WebKit x 12 widths, flows, axe WCAG 2.2 AA
```

`qa_http.py` ends with the brute-force check, which pauses logins for a minute; run it last.
Results are written to `runtime/qa/`. Delete that folder for a fresh database and index.
