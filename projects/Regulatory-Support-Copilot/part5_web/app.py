"""FastAPI website: run with `uvicorn part5_web.app:app --reload` from the project folder."""
import base64
import os
import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
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


@app.get("/healthz", include_in_schema=False)
def healthz():
    """Liveness check for the hosting platform (never needs the password)."""
    return {"status": "ok"}


@app.middleware("http")
async def require_password(request: Request, call_next):
    if not SITE_PASSWORD or request.url.path == "/healthz":
        return await call_next(request)
    header = request.headers.get("authorization", "")
    if header.lower().startswith("basic "):
        try:
            _, _, given = base64.b64decode(header[6:]).decode("utf-8").partition(":")
        except (ValueError, UnicodeDecodeError):
            given = ""
        if secrets.compare_digest(given.encode(), SITE_PASSWORD.encode()):
            return await call_next(request)
    return Response("Password required", status_code=401,
                    headers={"WWW-Authenticate": 'Basic realm="Copilot", charset="UTF-8"'})


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
