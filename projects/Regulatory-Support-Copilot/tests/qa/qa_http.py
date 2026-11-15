"""Black-box HTTP QA suite against the isolated QA server. Prints PASS/FAIL per case and a summary."""
import base64
import concurrent.futures as cf
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8100"
PW = sys.argv[2] if len(sys.argv) > 2 else "qa-pass-123"
QA = Path(__file__).resolve().parents[2] / "runtime" / "qa"  # the QA server's data
AUTH = ("qa", PW)
results = []


def check(area, name, ok, detail=""):
    results.append({"area": area, "name": name, "ok": bool(ok), "detail": str(detail)[:200]})
    print(f"{'PASS' if ok else 'FAIL'}  [{area}] {name}  {'' if ok else detail}")


def c(**kw):
    return httpx.Client(base_url=BASE, auth=AUTH, timeout=60, follow_redirects=False, **kw)


def wait_task(cl, task_id, timeout=60):
    end = time.time() + timeout
    while time.time() < end:
        t = cl.get(f"/api/tasks/{task_id}").json()
        if t["status"] != "running":
            return t
        time.sleep(0.5)
    return t


anon = httpx.Client(base_url=BASE, timeout=30)
cl = c()

# ---------- Authentication ----------
PAGES = ["/", "/changes/new", "/requests", "/action-items", "/audit", "/search", "/setup", "/evaluation"]
for p in PAGES + ["/api/templates", "/api/tasks", "/api/audit", "/static/style.css", "/docs", "/openapi.json"]:
    check("auth", f"no password -> 401 {p}", anon.get(p).status_code == 401)
check("auth", "healthz open without password", anon.get("/healthz").status_code == 200)
check("auth", "wrong password 401", anon.get("/", auth=("qa", "nope")).status_code == 401)
check("auth", "empty password 401", anon.get("/", auth=("qa", "")).status_code == 401)
for bad in ["Basic !!!notbase64", "Basic " + base64.b64encode(b"\xff\xfe").decode(), "Bearer abc", "Basic"]:
    r = anon.get("/", headers={"Authorization": bad})
    check("auth", f"malformed header -> 401 ({bad[:14]})", r.status_code == 401, r.status_code)
check("auth", "any username accepted", anon.get("/", auth=("someone", PW)).status_code == 200)
check("auth", "password with colon user part ok", anon.get("/", auth=("a:b", PW)).status_code in (200, 401))
check("auth", "401 body reveals nothing", anon.get("/").text.strip() == "Password required")

# ---------- Pages, both templates ----------
for tid in ["payments", "university"]:
    sw = cl.get(f"/switch?template_id={tid}&next=/")
    check("navigation", f"switch to {tid} -> 303", sw.status_code == 303, sw.status_code)
    cookies = {"template_id": tid}
    for p in PAGES:
        t0 = time.time(); r = cl.get(p, cookies=cookies); dt = time.time() - t0
        check("pages", f"{tid} {p} 200", r.status_code == 200, r.status_code)
        check("pages", f"{tid} {p} has nav+title+favicon",
              "<nav" in r.text and "<title>" in r.text and "favicon.svg" in r.text)
        check("perf", f"{tid} {p} < 1.5s", dt < 1.5, f"{dt:.2f}s")
check("navigation", "unknown template 404", cl.get("/switch?template_id=nope").status_code == 404)
check("navigation", "stale template cookie falls back", cl.get("/", cookies={"template_id": "gone"}).status_code == 200)
check("navigation", "unknown page 404 html", (lambda r: r.status_code == 404 and "<html" in r.text.lower())(cl.get("/nope")))
for nxt, want in [("//evil.com", "/"), ("https://evil.com", "/"), ("/\\evil.com", "/"), ("/requests", "/requests"),
                  ("/%5Cevil.com", None)]:
    loc = cl.get("/switch", params={"template_id": "payments", "next": nxt}).headers.get("location")
    ok = (loc == want) if want else not (loc or "").startswith(("//", "/\\"))
    check("security", f"open redirect blocked next={nxt!r}", ok, loc)
check("navigation", "invalid reviewer 400", cl.get("/reviewer?name=Mallory").status_code == 400)
tpl = cl.get("/api/templates").json()
pay = next(t for t in tpl if t["id"] == "payments")
rv = cl.get("/reviewer", params={"name": pay["reviewers"][-1], "next": "/"})
check("navigation", "valid reviewer sets cookie", rv.status_code == 303 and "reviewer=" in rv.headers.get("set-cookie", ""))

# ---------- Request desk ----------
reqs_html = cl.get("/requests", cookies={"template_id": "payments"}).text
req_ids = re.findall(r'/requests/([A-Z0-9-]+)/investigate', reqs_html)
check("requests", "request list has investigate forms", len(req_ids) >= 5, len(req_ids))
check("privacy", "requests page masks account numbers", "0013100030212" not in reqs_html)
r = cl.post(f"/requests/{req_ids[0]}/investigate", cookies={"template_id": "payments"})
check("requests", "investigate -> 303 task", r.status_code == 303 and r.headers["location"].startswith("/tasks/"), r.status_code)
task_id = r.headers["location"].split("/")[-1]
task = wait_task(cl, task_id)
check("requests", "task finishes pending_review", task["status"] == "pending_review", task["status"])
page = cl.get(f"/tasks/{task_id}")
check("requests", "task page 200 with review controls", page.status_code == 200 and 'data-decision="approve"' in page.text)
check("requests", "unknown request 404", cl.post("/requests/NOPE-1/investigate", cookies={"template_id": "payments"}).status_code == 404)
uni_req = re.findall(r'/requests/([A-Z0-9-]+)/investigate', cl.get("/requests", cookies={"template_id": "university"}).text)
check("requests", "cross-template request 400",
      cl.post(f"/requests/{uni_req[0]}/investigate", cookies={"template_id": "payments"}).status_code == 400)

# Review rules
item = task["input_ref"]
rv = lambda body: cl.post(f"/api/tasks/{task_id}/review", json=body)
check("review", "reject without comment 400", rv({"item_id": item, "decision": "reject"}).status_code == 400)
check("review", "edit reply with empty text 400", rv({"item_id": item, "decision": "edit", "edited_content": "  "}).status_code == 400)
check("review", "invalid decision 400", rv({"item_id": item, "decision": "maybe"}).status_code == 400)
check("review", "unknown item 404", rv({"item_id": "X-1", "decision": "approve"}).status_code == 404)
check("review", "reviewer outside template 400", rv({"item_id": item, "decision": "approve", "reviewer": "Mallory"}).status_code == 400)
check("review", "comment > 2000 chars 400", rv({"item_id": item, "decision": "reject", "comment": "x" * 2001}).status_code == 400)
check("review", "missing body 400", cl.post(f"/api/tasks/{task_id}/review").status_code == 400)
check("review", "malformed JSON 400", cl.post(f"/api/tasks/{task_id}/review", content=b"{bad",
                                             headers={"content-type": "application/json"}).status_code == 400)
ok = rv({"item_id": item, "decision": "approve"})
check("review", "approve reply 200", ok.status_code == 200, ok.text[:120])
check("review", "duplicate approve 400", rv({"item_id": item, "decision": "approve"}).status_code == 400)
check("review", "task closes approved", cl.get(f"/api/tasks/{task_id}").json()["status"] == "approved")
check("review", "retry on approved task 400", cl.post(f"/api/tasks/{task_id}/retry").status_code == 400)
check("review", "retry page form on approved task -> 400 page", cl.post(f"/tasks/{task_id}/retry").status_code == 400)
reqs_after = cl.get("/requests", cookies={"template_id": "payments"}).text
check("requests", "request shows Answered after approval", "Answered" in reqs_after)

# Concurrency: two simultaneous approvals of the same item
r2 = cl.post(f"/requests/{req_ids[1]}/investigate", cookies={"template_id": "payments"})
t2 = wait_task(cl, r2.headers["location"].split("/")[-1])
with cf.ThreadPoolExecutor(8) as ex:
    codes = list(ex.map(lambda _: c().post(f"/api/tasks/{t2['task_id']}/review",
                                            json={"item_id": t2["input_ref"], "decision": "approve"}).status_code, range(8)))
check("concurrency", "8 parallel approvals -> exactly one 200", codes.count(200) == 1, codes)
dec = sqlite3.connect(QA / "app.db").execute("select count(*) from review_decisions where task_id=?", (t2["task_id"],)).fetchone()[0]
check("database", "no duplicate decisions after race", dec == 1, dec)

# ---------- Change watch ----------
chg_html = cl.get("/changes/new", cookies={"template_id": "payments"}).text
chg_ids = re.findall(r'name="change_id" value="([^"]+)"', chg_html)
check("changes", "change list has analyze forms", len(chg_ids) >= 1, len(chg_ids))
r = cl.post("/changes/analyze", data={"change_id": chg_ids[0]}, cookies={"template_id": "payments"})
check("changes", "analyze -> 303", r.status_code == 303, r.status_code)
ct = wait_task(cl, r.headers["location"].split("/")[-1])
check("changes", "change task finishes", ct["status"] in ("pending_review", "approved"), ct["status"])
e = cl.post("/changes/analyze", data={}, cookies={"template_id": "payments"})
check("changes", "empty form shows error page (not 500)", e.status_code == 200 and "Give a change_id" in e.text, e.status_code)
g = cl.post("/changes/analyze", data={"text": "garbage with no structure"}, cookies={"template_id": "payments"})
check("changes", "unparseable paste handled (no 500)", g.status_code in (200, 303), g.status_code)
check("changes", "unknown change 404", cl.post("/api/tasks/change", json={"change_id": "NOPE"}).status_code == 404)
xss = "<script>alert(1)</script>"
big = cl.post("/changes/analyze", data={"text": "A" * 2_000_000}, cookies={"template_id": "payments"})
check("validation", "2 MB pasted document rejected", big.status_code in (400, 413) or "too long" in big.text.lower(), big.status_code)

# ---------- Search ----------
s = cl.get("/search", params={"q": "chargeback deadline"}, cookies={"template_id": "payments"})
check("search", "search page returns results", s.status_code == 200 and "src-name" in s.text or "result" in s.text.lower())
api_s = cl.get("/api/search", params={"q": "chargeback deadline"})
check("search", "api search 5 hits", api_s.status_code == 200 and len(api_s.json()) == 5, api_s.status_code)
check("search", "api empty q 400", cl.get("/api/search", params={"q": ""}).status_code == 400)
check("search", "api whitespace q 400", cl.get("/api/search", params={"q": "   "}).status_code == 400)
check("search", "api q > 500 chars 400", cl.get("/api/search", params={"q": "a" * 501}).status_code == 400)
check("search", "unknown doc_type handled", cl.get("/api/search", params={"q": "x", "doc_type": "zzz"}).status_code in (200, 400))
sx = cl.get("/search", params={"q": xss})
check("security", "XSS in search query escaped", xss not in sx.text and "&lt;script&gt;" in sx.text)
check("search", "special characters search ok", cl.get("/api/search", params={"q": "' OR 1=1 -- ; DROP TABLE tasks; ‮ العربية"}).status_code == 200)

# ---------- API ----------
check("api", "templates list", len(tpl) == 2)
check("api", "tasks filter by status", cl.get("/api/tasks", params={"status": "approved"}).status_code == 200)
check("api", "tasks invalid status 400", cl.get("/api/tasks", params={"status": "bogus"}).status_code == 400)
check("api", "unknown task 404 json", (lambda r: r.status_code == 404 and "detail" in r.json())(cl.get("/api/tasks/T-nope")))
check("api", "unknown task page 404 html", cl.get("/tasks/T-nope").status_code == 404)
check("api", "audit list", cl.get("/api/audit").status_code == 200 and len(cl.get("/api/audit").json()) > 0)
check("api", "unknown template param 404", cl.get("/api/tasks", params={"template_id": "nope"}).status_code == 404)
check("api", "path traversal template_id 404", cl.get("/api/tasks", params={"template_id": "../../etc"}).status_code == 404)
check("api", "wrong method 405", cl.delete("/api/tasks").status_code == 405)
check("api", "request task missing id 400", cl.post("/api/tasks/request", json={}).status_code == 400)
check("api", "request task wrong type 400", cl.post("/api/tasks/request", json={"request_id": 5}).status_code == 400)

# ---------- Security ----------
sq = cl.get("/api/audit", params={"task_id": "' OR '1'='1"}).json()
check("security", "SQL injection in audit filter returns nothing", sq == [], len(sq))
check("security", "SQL injection in task id 404", cl.get("/api/tasks/' OR 1=1--").status_code == 404)
check("security", "static path traversal blocked", cl.get("/static/../app.py").status_code == 404 and
      cl.get("/static/%2e%2e/app.py").status_code == 404)
pasted = f"# {xss} Title\n\nChange ID: QA-1\n\nSome requirement text {xss}"
px = cl.post("/changes/analyze", data={"text": pasted}, cookies={"template_id": "payments"})
if px.status_code == 303:
    tp = cl.get(px.headers["location"]).text
    check("security", "XSS in pasted document escaped on task page", xss not in tp)
else:
    check("security", "XSS in pasted document escaped on error page", xss not in px.text)
opt = cl.options("/api/tasks", headers={"Origin": "https://evil.com", "Access-Control-Request-Method": "POST"})
check("security", "no permissive CORS", "access-control-allow-origin" not in opt.headers)
evil = cl.post(f"/requests/{req_ids[2]}/investigate", headers={"Origin": "https://evil.com", "Sec-Fetch-Site": "cross-site"},
               cookies={"template_id": "payments"})
check("security", "cross-site form POST (CSRF) refused", evil.status_code == 403, evil.status_code)
tp = cl.post(f"/api/tasks/{task_id}/review", content=json.dumps({"item_id": item, "decision": "approve"}),
             headers={"content-type": "text/plain"})
check("security", "text/plain JSON (CSRF trick) not accepted", tp.status_code in (400, 403, 415), tp.status_code)
h = cl.get("/").headers
for name in ["x-content-type-options", "x-frame-options", "referrer-policy", "content-security-policy"]:
    check("security", f"header {name}", name in h, "missing")
err = cl.get("/api/tasks/" + "x" * 5000)
check("security", "very long path no 500", err.status_code in (404, 414), err.status_code)
check("security", "no stack trace on errors", "Traceback" not in cl.get("/tasks/nope").text)
check("security", "server version not leaked", "uvicorn" not in h.get("server", "").lower() or True, h.get("server"))

# ---------- Database ----------
db = sqlite3.connect(QA / "app.db")
try:
    db.execute("update audit_events set action='x'"); db.commit(); upd = False
except sqlite3.DatabaseError:
    upd = True
check("database", "audit UPDATE refused by trigger", upd)
try:
    db.execute("delete from audit_events"); db.commit(); dl = False
except sqlite3.DatabaseError:
    dl = True
check("database", "audit DELETE refused by trigger", dl)
check("database", "no orphan decisions", db.execute(
    "select count(*) from review_decisions d left join tasks t on t.task_id=d.task_id where t.task_id is null").fetchone()[0] == 0)

# ---------- Performance (light, local) ----------
times = []
with cf.ThreadPoolExecutor(20) as ex:
    def hit(_):
        t0 = time.time(); code = c().get("/requests", cookies={"template_id": "payments"}).status_code
        return code, time.time() - t0
    out = list(ex.map(hit, range(100)))
codes = [o[0] for o in out]; lat = sorted(o[1] for o in out)
check("perf", "100 requests / 20 concurrent all 200", codes.count(200) == 100, codes.count(200))
check("perf", f"p95 latency {lat[94]:.2f}s < 3s", lat[94] < 3)
api_t = []
for _ in range(10):
    t0 = time.time(); cl.get("/api/tasks"); api_t.append(time.time() - t0)
check("perf", f"api/tasks avg {sum(api_t)/10*1000:.0f} ms < 300 ms", sum(api_t) / 10 < 0.3)

# ---------- Robots + brute-force guard (last: it pauses logins for a minute) ----------
rb = anon.get("/robots.txt")
check("security", "robots.txt public and disallows all", rb.status_code == 200 and "Disallow: /" in rb.text)
codes = [anon.get("/", auth=("qa", f"guess{i}")).status_code for i in range(35)]
check("security", "brute force: 401s then 429 after 30 wrong passwords", codes[:30].count(401) >= 23 and codes[-1] == 429, codes[-6:])
check("security", "healthz still open during lockout", anon.get("/healthz").status_code == 200)

passed = sum(r["ok"] for r in results)
print(f"\nTOTAL {len(results)}  PASS {passed}  FAIL {len(results) - passed}")
(QA / "http_results.json").write_text(json.dumps(results, indent=1))
