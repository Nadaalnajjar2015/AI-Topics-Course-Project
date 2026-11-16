"""Browser security: CSRF guard, security headers, safe redirects, one index rebuild at a time."""
from part5_web import api


def test_cross_site_posts_are_refused(client):
    for headers in ({"Sec-Fetch-Site": "cross-site"}, {"Sec-Fetch-Site": "same-site"},
                    {"Origin": "https://evil.example"}):
        response = client.post("/requests/P-REQ-001/investigate", headers=headers, follow_redirects=False)
        assert response.status_code == 403, headers
        assert client.post("/api/tasks/request", json={"request_id": "P-REQ-001"}, headers=headers).status_code == 403


def test_same_site_posts_still_work(client, sync_tasks):
    for headers in ({"Sec-Fetch-Site": "same-origin"}, {"Origin": "http://testserver"}, {}):
        response = client.post("/requests/P-REQ-001/investigate", headers=headers, follow_redirects=False)
        assert response.status_code == 303, headers


def test_cross_site_reads_are_allowed(client):
    assert client.get("/requests", headers={"Sec-Fetch-Site": "cross-site"}).status_code == 200


def test_security_headers_on_pages_errors_and_static(client):
    for path in ("/", "/nope", "/static/style.css", "/api/tasks/T-none"):
        headers = client.get(path).headers
        assert headers["x-content-type-options"] == "nosniff"
        assert headers["x-frame-options"] == "DENY"
        assert headers["referrer-policy"] == "same-origin"
        assert "script-src 'self'" in headers["content-security-policy"]
    assert "content-security-policy" not in client.get("/docs").headers  # Swagger UI loads its own scripts


def test_pages_have_no_inline_scripts_or_handlers(client):
    for path in ("/", "/requests", "/changes/new", "/setup", "/search", "/audit", "/action-items"):
        html = client.get(path).text
        assert "<script>" not in html and "onchange=" not in html and 'style="' not in html, path


def test_switch_next_only_allows_same_site_paths(client):
    for target, expected in (("/requests", "/requests"), ("//evil.example", "/"), ("/\\evil.example", "/"),
                             ("https://evil.example", "/"), ("/a\\b", "/")):
        response = client.get("/switch", params={"template_id": "payments", "next": target}, follow_redirects=False)
        assert response.headers["location"] == expected, target


def test_only_one_index_rebuild_at_a_time(client):
    assert api._REBUILD.acquire(blocking=False)
    try:
        response = client.post("/api/index/rebuild", json={"template_id": "payments"})
        assert response.status_code == 409 and "already running" in response.json()["detail"]
    finally:
        api._REBUILD.release()
