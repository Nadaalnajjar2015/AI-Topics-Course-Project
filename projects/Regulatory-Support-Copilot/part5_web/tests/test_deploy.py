"""Production entry point: health check, optional password gate, index bootstrap."""
import base64

from part5_web import app as app_module
from part5_web import serve


def _basic(password: str) -> dict:
    return {"Authorization": "Basic " + base64.b64encode(f"user:{password}".encode()).decode()}


def test_healthz_is_open(client):
    assert client.get("/healthz").json() == {"status": "ok"}


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
