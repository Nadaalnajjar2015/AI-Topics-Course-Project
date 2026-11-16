"""FastAPI website: run with `uvicorn part5_web.app:app --reload` from the project folder."""
import base64
import os
import secrets
import time
from collections import deque
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from part1_templates.tools.templates import load_template
from part2_knowledge.common.config import settings
from part5_web import api, pages
from part5_web.context import active_template, page

app = FastAPI(title="Regulatory & Support Copilot", description="Prototype – mock data")
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")
app.include_router(api.router)
app.include_router(pages.router)

# Optional access gate for a public deployment: set SITE_PASSWORD (any username works).
# Without it the site stays open, as in local development and the tests.
SITE_PASSWORD = os.environ.get("SITE_PASSWORD", "")
# Brute-force guard: after MAX_FAILURES wrong passwords within FAILURE_WINDOW seconds, password
# checks pause (429) until the window clears. Site-wide on purpose: client IPs behind the host's
# proxy come from X-Forwarded-For, which an attacker can fake.
MAX_FAILURES, FAILURE_WINDOW = 30, 60.0
_failures: deque = deque()


def _locked(now: float) -> bool:
    while _failures and now - _failures[0] > FAILURE_WINDOW:
        _failures.popleft()
    return len(_failures) >= MAX_FAILURES


@app.get("/healthz", include_in_schema=False)
def healthz():
    """Liveness check for the hosting platform (never needs the password)."""
    return {"status": "ok"}


@app.get("/robots.txt", include_in_schema=False)
def robots():
    """A private tool: ask search engines not to index anything."""
    return PlainTextResponse("User-agent: *\nDisallow: /\n")


PUBLIC_PATHS = {"/healthz", "/robots.txt"}  # answered without the site password


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Browsers ask for /favicon.ico by default; send them the SVG icon."""
    return RedirectResponse("/static/favicon.svg", status_code=301)


@app.middleware("http")
async def require_password(request: Request, call_next):
    if not SITE_PASSWORD or request.url.path in PUBLIC_PATHS:
        return await call_next(request)
    header = request.headers.get("authorization", "")
    if header.lower().startswith("basic "):
        now = time.monotonic()
        if _locked(now):
            return Response("Too many wrong passwords; wait a minute and try again", status_code=429,
                            headers={"Retry-After": str(int(FAILURE_WINDOW))})
        try:
            _, _, given = base64.b64decode(header[6:]).decode("utf-8").partition(":")
        except (ValueError, UnicodeDecodeError):
            given = ""
        if secrets.compare_digest(given.encode(), SITE_PASSWORD.encode()):
            return await call_next(request)
        _failures.append(now)
    return Response("Password required", status_code=401,
                    headers={"WWW-Authenticate": 'Basic realm="Copilot", charset="UTF-8"'})


SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
CSP = ("default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
       "connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'self'; object-src 'none'")
DOC_PATHS = ("/docs", "/redoc", "/openapi.json")  # FastAPI's API docs load their own scripts


def _cross_site(request: Request) -> bool:
    """True when a state-changing request comes from another website (CSRF).

    Browsers send Basic-auth credentials and cookies with cross-site form posts, so every
    POST must come from this site: Sec-Fetch-Site first, then the Origin header.
    """
    fetch_site = request.headers.get("sec-fetch-site")
    if fetch_site:
        return fetch_site not in ("same-origin", "none")
    origin = request.headers.get("origin")
    if origin:
        return origin.split("://", 1)[-1].rstrip("/") != request.headers.get("host", "")
    return False  # non-browser clients (tests, curl) send neither header


@app.middleware("http")
async def security(request: Request, call_next):
    """Refuse cross-site writes and add browser security headers to every response."""
    if request.method not in SAFE_METHODS and _cross_site(request):
        response = Response("Cross-site request refused", status_code=403)
    else:
        response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    if not request.url.path.startswith(DOC_PATHS):
        response.headers.setdefault("Content-Security-Policy", CSP)
    if request.url.scheme == "https":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
    return response


def _wants_json(request: Request) -> bool:
    return request.url.path.startswith("/api/")


def _error_page(request: Request, status: int, message: str):
    try:
        template = active_template(request)
    except HTTPException:
        template = load_template(settings.active_template)
    response = page(request, "error.html", template, status=status, message=message)
    response.status_code = status
    return response


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, error: StarletteHTTPException):
    if _wants_json(request):
        return JSONResponse({"detail": error.detail}, status_code=error.status_code)
    return _error_page(request, error.status_code, str(error.detail))


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, error: RequestValidationError):
    """Invalid input is a 400 with a readable message, for pages and the API alike."""
    problems = "; ".join(f"{'.'.join(str(p) for p in e['loc'][1:]) or 'body'}: {e['msg']}"
                         for e in error.errors())
    message = f"Invalid input – {problems}"
    if _wants_json(request):
        return JSONResponse({"detail": message}, status_code=400)
    return _error_page(request, 400, message)
