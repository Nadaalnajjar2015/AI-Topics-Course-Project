"""Production entry point: health check, optional password gate, index bootstrap."""
import base64

from part5_web import app as app_module
from part5_web import serve


def _basic(password: str) -> dict:
    return {"Authorization": "Basic " + base64.b64encode(f"user:{password}".encode()).decode()}


def test_healthz_is_open(client):
    assert client.get("/healthz").json() == {"status": "ok"}


def test_favicon_is_linked_and_served(client):
    assert '/static/favicon.svg' in client.get("/").text
    icon = client.get("/static/favicon.svg")
    assert icon.status_code == 200 and icon.headers["content-type"].startswith("image/svg+xml")
    legacy = client.get("/favicon.ico", follow_redirects=False)
    assert legacy.status_code == 301 and legacy.headers["location"] == "/static/favicon.svg"


def test_site_is_open_without_password(client):
    assert client.get("/").status_code == 200


def test_password_gate_when_configured(client, monkeypatch):
    monkeypatch.setattr(app_module, "SITE_PASSWORD", "s3cret")
    denied = client.get("/requests")
    assert denied.status_code == 401 and "Basic" in denied.headers["www-authenticate"]
    assert client.get("/api/templates").status_code == 401
    assert client.get("/requests", headers=_basic("wrong")).status_code == 401
    assert client.get("/requests", headers=_basic("s3cret")).status_code == 200
    assert client.get("/healthz").status_code == 200  # the host's health check needs no password


def test_ensure_index_builds_only_missing_templates(monkeypatch):
    calls = []
    monkeypatch.setattr(serve, "indexed_chunks", lambda tid: 0 if tid == "university" else 89)
    monkeypatch.setattr(serve.subprocess, "run", lambda args, check: calls.append(args))
    serve.ensure_index()
    assert len(calls) == 1 and calls[0][-2:] == ["--template", "university"]
    assert calls[0][1:3] == ["-m", "part2_knowledge.knowledge_base.ingest"]


def test_too_many_wrong_passwords_pause_logins(client, monkeypatch):
    monkeypatch.setattr(app_module, "SITE_PASSWORD", "s3cret")
    monkeypatch.setattr(app_module, "_failures", __import__("collections").deque())
    monkeypatch.setattr(app_module, "MAX_FAILURES", 3)
    for _ in range(3):
        assert client.get("/requests", headers=_basic("guess")).status_code == 401
    locked = client.get("/requests", headers=_basic("s3cret"))
    assert locked.status_code == 429 and locked.headers["retry-after"] == "60"
    assert client.get("/healthz").status_code == 200
    monkeypatch.setattr(app_module.time, "monotonic", lambda: 10**9)  # the window has passed
    assert client.get("/requests", headers=_basic("s3cret")).status_code == 200


def test_requests_without_a_password_do_not_count_as_failures(client, monkeypatch):
    monkeypatch.setattr(app_module, "SITE_PASSWORD", "s3cret")
    monkeypatch.setattr(app_module, "_failures", __import__("collections").deque())
    for _ in range(40):  # every browser first asks without a password
        assert client.get("/").status_code == 401
    assert client.get("/requests", headers=_basic("s3cret")).status_code == 200


def test_robots_txt_is_public_and_blocks_indexing(client, monkeypatch):
    monkeypatch.setattr(app_module, "SITE_PASSWORD", "s3cret")
    response = client.get("/robots.txt")
    assert response.status_code == 200 and "Disallow: /" in response.text
