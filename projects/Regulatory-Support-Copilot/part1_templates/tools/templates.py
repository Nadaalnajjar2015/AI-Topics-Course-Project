"""Discover and validate organization templates."""
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

import yaml

from contracts.schemas import TemplateConfig

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _settings():
    """Use Part 2's settings when present; allow explicit IDs before integration."""
    try:
        return import_module("part2_knowledge.common.config").settings
    except ModuleNotFoundError as exc:
        if exc.name != "part2_knowledge.common.config":
            raise
        return SimpleNamespace(active_template="payments", templates_dir="part1_templates/templates")


def _templates_root() -> Path:
    path = Path(_settings().templates_dir)
    return path if path.is_absolute() else _PROJECT_ROOT / path


def _available() -> dict[str, Path]:
    return {path.parent.name: path for path in sorted(_templates_root().glob("*/template.yaml"))}


def load_template(template_id=None) -> TemplateConfig:
    """Load an explicit template, or Part 2's active template (default payments)."""
    template_id = _settings().active_template if template_id is None else template_id
    available = _available()
    if template_id not in available:
        raise KeyError(f"Template {template_id!r} not found; available templates: {', '.join(available)}")
    template = TemplateConfig.model_validate(yaml.safe_load(available[template_id].read_text(encoding="utf-8")))
    if template.id != template_id:
        raise ValueError(f"Template ID {template.id!r} does not match folder {template_id!r}")
    return template


def list_templates(template_id=None) -> list[TemplateConfig]:
    """List all templates for discovery, or an explicitly selected template."""
    if template_id is not None:
        return [load_template(template_id)]
    return [load_template(identifier) for identifier in _available()]
