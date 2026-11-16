# QA report: Regulatory & Support Copilot website

- **Date:** 2026-11-16
- **Build tested:** branch `part5/web`: fixes `b5991e1`, then live-site fixes `8710c8c`, `7f36981` and the Groq message change
- **Live site:** https://regulatory-support-copilot.onrender.com (Render free plan)

## 1. Scope and method

| Area | What was tested |
| --- | --- |
| Application | FastAPI + Jinja2 server pages, vanilla JS (`ui.js`, `task.js`), JSON API `/api/*`, SQLite (tasks, review decisions, append-only audit log), Chroma vector index, Part 1 JSON state |
| Pages | Overview, Central bank circulars (changes), Bank support tickets (requests), Task page, Action Items, Audit Log, Knowledge Search, Setup, Evaluation, error pages; both organizations (payments, university) |
| API | 10 endpoints: templates, tasks (list/get/start change/start request/review/retry), search, index rebuild, audit |
| Environment | **Isolated QA server**: the production entry point (`python -m part5_web.serve`) with its own empty database, index and Part 1 state, site password on, fake model. Production data was never touched |
| Production | 22 checks without the password, then 333 logged-in browser checks and API checks with the password (shared later). Writes kept to the minimum: 1 investigation, 1 approval, 1 circular analysis (+2 retries), 1 index rebuild. No load or brute-force test on production |

Tools: pytest, httpx (HTTP suite), Playwright 1.49 with Microsoft Edge (Chromium), Firefox and WebKit, axe-core 4.10 (WCAG 2.2 AA), Lighthouse 12.3, pip-audit 2.7, git secret scan, Windows process memory counters.

## 2. Results summary

| Suite | Cases | Passed | Failed | Notes |
| --- | --- | --- | --- | --- |
| Unit + integration (pytest, whole project) | 534 | 534 | 0 | 12 new regression tests for the fixes below |
| HTTP black-box (`tests/qa/qa_http.py`) | 156 | 156 | 0 | first run: 147/153 (6 real findings) |
| Browser (`tests/qa/e2e.js`), 3 engines × 12 widths | 701 | 701 | 0 | first run surfaced overflow, contrast, keyboard, font-size bugs |
| Lighthouse (8 page/device runs + 1 rerun) | 9 | 9 | 0 | Performance 96–100, Accessibility 100, Best Practices 100 |
| Dependency scan (pip-audit, 120 packages) | 1 | 1 | 0 | 4 advisories in chromadb, not reachable (see 5) |
| Secret scan (Git history + tracked files) | 1 | 1 | 0 | no keys; `.env` and `runtime/` ignored |
| Production, logged in (3 engines × 3 widths × 2 organizations × 8 pages, axe, real Groq flows) | 333 | 331 | 2 | both explained in section 7 (test false positive; Groq daily limit) |
| Production, without password | 22 | 22 | 0 | |
| **Total executed (final run)** | **1,402** | **1,402** | **0** | plus production checks in section 7 |

Blocked or not executed: see section 8.

## 3. Bugs found and fixed

| # | Severity | Bug | Root cause | Fix | Retest |
| --- | --- | --- | --- | --- | --- |
| 1 | **High** | Setup → **Rebuild index** raised server memory from 262 MB to **697 MB** and kept it there. On the 512 MB free host this kills the instance, which also wipes all tasks and audit events | `ingest_all` embedded every chunk in one ONNX call | Embed 4 chunks per call (`EMBED_BATCH`); measured peak 318 MB in the server, 255 MB standalone | Memory re-measured; search works after rebuild; `test_embeddings_are_computed_in_small_batches` |
| 2 | Medium | Two rebuilds at once would double memory and race on the same collection | No guard | One rebuild at a time, second gets 409 | `test_only_one_index_rebuild_at_a_time` |
| 3 | Medium | **CSRF**: another website could make a logged-in browser start investigations/analyses (Groq cost, audit noise) | Browsers resend Basic-auth credentials on cross-site form posts; no origin check | Refuse POSTs whose `Sec-Fetch-Site`/`Origin` is another site (403) | `test_cross_site_posts_are_refused`, same-site posts still 303 |
| 4 | Medium | No security headers: page could be framed (clickjacking), no CSP | Not configured | CSP (`script-src 'self'`, no inline), `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy`, HSTS on HTTPS; inline scripts/handlers moved to `ui.js` | header tests, 0 CSP violations in 3 browsers |
| 5 | Medium | Unlimited password guessing | No throttle | After 30 wrong passwords per minute, logins pause (429 + `Retry-After`) | 2 unit tests + live HTTP check |
| 6 | Medium | Tablets (760–1024 px): page scrolled sideways and the Status/**Investigate** column was cut off | Screen-reader-only labels (`position:absolute`) escaped the table's scroll box; desktop table layout used down to 760 px | `.table-wrap` is the positioning context; card layout up to 1024 px | 0 overflow at 12 widths × 8 pages × 3 engines; screenshots checked |
| 7 | Medium | Mobile **Menu** could not be opened with the keyboard | It was a `<label>`, not a button | Real `<button>` with `aria-expanded`/`aria-controls`, Escape returns focus | e2e menu test in 3 engines |
| 8 | Low | Text contrast 4.27–4.39:1 on tinted panels, task ID 2.56:1 (WCAG AA needs 4.5) | Grey `#64748b` too light | `--text-3: #566578` (≥ 5.16:1 on every panel colour) | axe: 0 violations on all pages |
| 9 | Low | Text under 11 px (sidebar label 10.5 px, code in small print 10.75 px) | Font sizes | 11 px minimum | e2e font-size check |
| 10 | Low | `next=/\evil.com` accepted by the redirect filter (not exploitable: the server encodes `\`) | Filter only checked `//` | Reject any backslash | `test_switch_next_only_allows_same_site_paths` |
| 11 | Low | No `robots.txt` / description | Not present | `robots.txt` disallows indexing (private tool), meta description | Lighthouse, unit test |
| 12 | **High** (live only) | Every knowledge search took **4.5–5.8 s on Render** (0.1 s locally); investigations and change analyses search several times | (a) a new Chroma client (settings + `.env` re-read) was built per search; (b) ONNX Runtime starts one thread per physical core of the host, and in a 0.1-CPU container those threads fight for one small slice | Cache one client per index folder; run the MiniLM model on 1 ONNX thread (same model and name, existing indexes valid) | Live: 0.76–1.15 s per search (one 11.8 s outlier right after deploy); pages 1.3–1.9 s |
| 13 | Medium | When Groq's **daily** token allowance runs out, the task said only "rate limit exhausted", so reviewers kept pressing Retry | Every 429 got the same text | Daily limits now say so and that retrying now will not help; Groq's raw message (with the account ID) is still never shown | `test_daily_rate_limit_is_named_without_leaking_the_body` |

Test-script defects found along the way (Firefox's first 401 before sending the password, Playwright helpers blocked by the new CSP, timing waits) were fixed in the scripts, not the app.

## 4. Functional coverage (all passed after fixes)

- **Authentication:** 401 on every page, API, static file and API docs without the password; wrong, empty, malformed (`Basic !!!`, invalid UTF-8, `Bearer`) headers → 401, never 500; any username accepted; 401 body reveals nothing; `/healthz` and `/robots.txt` public; lockout and recovery.
- **Navigation:** every sidebar link (both organizations), organization and reviewer switchers, unknown page 404 (HTML), stale cookie fallback, open-redirect attempts (`//`, `https://`, `/\`).
- **Bank support tickets:** list (masking: no account numbers/IBANs shown), status filters, text filter, empty state, Investigate → task page → Approve → task Approved and ticket Answered; unknown ticket 404; ticket of the other organization 400.
- **Review rules:** reject without comment 400 (and inline message in the UI), empty edited reply 400, invalid decision 400, unknown item 404, reviewer from another organization 400, comment > 2,000 chars 400, missing/malformed body 400, duplicate decision 400, retry of a non-failed task 400.
- **Concurrency:** 8 simultaneous approvals of one item → exactly one 200, one decision row in the database.
- **Central bank circulars:** Analyze → task page; empty form → error message (no 500); unparseable paste handled; 2 MB paste rejected; unknown change 404.
- **Search:** page and API (5 hits), empty/whitespace query 400, > 500 chars 400, unknown type handled, quotes/SQL/Arabic/RTL characters OK, header search box.
- **Audit log:** lists events; SQL injection in the filter returns nothing; UPDATE and DELETE refused by database triggers.
- **Setup:** rebuild button works (now through `ui.js`), chunk counts.
- **Production start:** empty disk → both indexes built (89 + 63 chunks) before serving.

## 5. Security findings

| Check | Result |
| --- | --- |
| SQL injection (task ID, audit filter, search) | Not vulnerable (parameterised queries) |
| XSS (search query, pasted document title/body) | Escaped (Jinja autoescape; JS uses `textContent`); CSP now blocks inline script as a second layer |
| CSRF | **Fixed** (#3). JSON sent as `text/plain` is also rejected (400) |
| Broken access control / IDOR | Task IDs are random 128-bit; cross-organization IDs refused. All users share one password (see 6) |
| Path traversal (`template_id=../..`, `/static/../app.py`) | 404 |
| CORS | No `Access-Control-Allow-Origin` returned |
| Secrets | None in Git history, frontend or responses; keys only in Render's environment |
| Error handling | No stack traces; 404/400 pages are styled; 5,000-char path → 404 |
| Dependencies | pip-audit: 4 advisories in `chromadb` 1.5.9 (CVE-2026-45829, -45830, -45831, -45833), no fixed version yet. All are in Chroma's **network server API** and its multi-tenant permissions; this project only uses the embedded `PersistentClient` and never runs that server, so they are not reachable. Upgrade when a fix ships |

## 6. Remaining issues (documented, not fixed)

| Severity | Issue | Why not fixed / recommendation |
| --- | --- | --- |
| Medium | One shared site password; the "Reviewer" picker is not a login, so audit entries record a chosen name, not a verified person; Basic auth has no logout (close the browser) | Needs real user accounts: an architectural change outside this audit. Fine for a class demo; required before real use |
| Medium | Free plan: the SQLite database resets on every restart/deploy; site sleeps after 15 min idle (first visit about 1 min) | Hosting limit. Persistent storage needs a paid disk or an external database (changes Part 4's storage) |
| Low | `chromadb` advisories (section 5) | Not reachable; upgrade when fixed |
| Low | An attacker who knows the URL can trigger the 1-minute login pause | Deliberate trade-off: per-IP limits can be bypassed behind the proxy. Use a long password |
| Low | Once a ticket/circular has a result, the list offers **View result** only; re-running is possible only for failed tasks (Retry) | Current design; a "Run again" button is a product decision |
| Low | Organization/reviewer switch use GET links, so a link on another site could change the viewer's selected organization | Harmless (view preference only, cookie `SameSite=Lax`) |
| Medium | Groq free plan: **200,000 tokens per day per Groq account** (all keys of the account share it). Yesterday's evaluation used it up, so on the test day circular analyses failed on the live site | Do not run the evaluation on demo day, or use a separate Groq account for the evaluation; the allowance frees up over a rolling 24 hours |

## 7. Production checks (read-only)

Run after Render deployed `b5991e1`, without the password and without changing anything. 22 checks, all as expected.

| Check | Result |
| --- | --- |
| Health check `/healthz` | 200, 0.26–0.28 s warm |
| HTTPS | `http://` → 301 to `https://`; certificate accepted by curl's default verification; HSTS `max-age=31536000` |
| Password gate | 401 on `/`, `/requests`, `/tasks/x`, `/api/templates`, `/api/tasks`, `/static/*`, `/favicon.ico`, `/docs`, `/openapi.json`; body only "Password required"; one wrong password → 401 |
| CSRF guard | cross-site POST → 403; foreign `Origin` → 403; the site's own `Origin` passes through to the password check (proves the host name matches behind Render's proxy) |
| Headers | CSP, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy: same-origin` on every response |
| CORS | no `Access-Control-Allow-Origin` on a foreign preflight |
| `robots.txt` | public, `Disallow: /` |

**Logged in (password provided by the owner):**

| Check | Result |
| --- | --- |
| All 8 pages × 2 organizations × Edge, Firefox, WebKit × 375/768/1366 px | 200, heading and favicon present, no sideways scroll, no console/JS/CSP/HTTP errors |
| Accessibility (axe WCAG 2.2 AA, 8 pages) | 0 violations |
| Page load (desktop, full render) | 1.3–1.9 s |
| API | templates, tasks, search (5 hits), 400 on empty query/bad status, 404 unknown task |
| Investigation with the real model (Groq `gpt-oss-20b`) | finished, correct root cause (AC01) and draft reply; no account numbers or IBANs on the page |
| Review | reject without comment blocked; approve closes the task; audit log records both |
| Index rebuild on the 512 MB instance | completed, site stayed up, search works afterwards (confirms fix #1) |
| Circular analysis with the real model | **Failed: Groq daily token limit** (199,336 of 200,000 used by the earlier evaluation). The page showed Failed with Retry, as designed; Retry worked but hit the same limit |
| Privacy check on the task page | first flagged by the test, then confirmed a **false positive** (adjacent numbers joined without spaces); server HTML has no account numbers or IBANs |

## 8. Blocked or not executed

| Item | Reason |
| --- | --- |
| Circular analysis with the real model on the live site | Blocked by Groq's daily token limit on the test day; works with the fake model and passed in the evaluation run |
| Load/stress test on production | Forbidden by the brief (free instance, 0.1 CPU); light load done locally: 100 requests, 20 concurrent, all 200, p95 < 3 s |
| Real Safari (macOS/iOS) and Google Chrome | Not available on this Windows machine; tested WebKit (Safari's engine) and Edge (Chromium, same engine as Chrome) |
| Real screen reader (NVDA/VoiceOver) | Not available; covered by axe-core, semantic HTML, labels, keyboard and focus tests |
| Offline / slow-network behaviour | Not simulated; `task.js` retries polling every 5 s on network errors (code review only) |
| Real AI model in the QA run | Fake model used to avoid spending the Groq quota; Groq paths covered by the evaluation run and Part 2 tests |
| File upload, pagination, sorting, email fields, logout | Features do not exist in this application |

## 9. Performance

- Lighthouse mobile: FCP/LCP 1.1–1.2 s, TBT 0 ms, CLS 0; desktop 0.3 s. Page weight 46–67 KB (no images, 2 small JS files, 1 CSS file).
- Local server: pages under 1.5 s, `/api/tasks` average < 300 ms, 100 requests at 20 concurrency all succeed.
- Memory: about 265 MB while serving, 318 MB peak during an index rebuild (was 697 MB).
- Live (Render free, 0.1 CPU): pages 1.3–1.9 s fully rendered, search 0.76–1.15 s (was 4.5–5.8 s), first visit after 15 min idle about 1 minute.

## 10. Overall assessment

All Critical and High issues are fixed and retested; no test fails. Functionally, the website behaves as documented in both organizations, and security, layout and accessibility are at a good level (Lighthouse Accessibility 100, axe 0 violations, no horizontal scrolling from 320 to 2560 px in three browser engines). It is **ready for a class demo and a supervised pilot**. It is **not yet production-ready for real bank data** because of the two Medium items in section 6: shared password without individual accounts, and non-persistent storage on the free plan.

## How to re-run

See `tests/qa/README.md`. Unit/integration: `python -m pytest -q`.
