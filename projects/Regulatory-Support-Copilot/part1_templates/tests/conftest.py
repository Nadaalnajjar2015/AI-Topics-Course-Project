"""Part 1 tests isolate runtime writes and use fakes only for missing teammates."""
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
import pytest

from contracts import schemas
from part1_templates.tools import _files

TEMPLATES = Path(__file__).resolve().parents[1] / "templates"


@pytest.fixture(params=["payments", "university"])
def template_id(request):
    return request.param


@pytest.fixture(autouse=True)
def isolated_runtime(tmp_path, monkeypatch):
    path = tmp_path / "runtime"
    monkeypatch.setattr(_files, "_RUNTIME_ROOT", path)
    return path


class ActionItemFake(BaseModel):
    """Test-only shape from Guide 8.1; never substitutes a production contract."""

    action_id: str
    change_id: str
    title: str
    description: str
    unit_id: str
    stakeholders: list[str]
    owner_role: str
    due_before: date | None
    checks: list[dict]
    sources: list[dict]
    status: Literal["pending_review", "approved", "rejected"]


@pytest.fixture
def action_model(monkeypatch):
    monkeypatch.setattr(schemas, "ActionItem", ActionItemFake, raising=False)
    return ActionItemFake
