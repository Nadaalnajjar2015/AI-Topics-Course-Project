"""Render organization vocabulary without expanding inserted source text."""
from pathlib import Path
from string import Formatter

from contracts.schemas import TemplateConfig


def render(prompt_text: str, template: TemplateConfig, **extra) -> str:
    """Fill template labels and extra named values; name unknown placeholders."""
    values = {"organization": template.organization, "prompt_hints": template.prompt_hints}
    for key, label in template.labels.items():
        if key in {"units", "stakeholders"}:
            values[f"{key[:-1]}_label_plural"] = label
        else:
            values[f"{key}_label"] = label
    if "reviewer" in template.labels:
        values["reviewer"] = template.labels["reviewer"]
    values.update(extra)
    for _, name, _, _ in Formatter().parse(prompt_text):
        if name is not None and name not in values:
            raise ValueError(f"Unknown prompt placeholder: '{name}'.")
    try:
        return prompt_text.format_map(values)
    except KeyError as exc:
        raise ValueError(f"Unknown prompt placeholder: '{exc.args[0]}'.") from exc


def load_prompt(path: str | Path) -> str:
    """Read a prompt file as UTF-8; relative paths use the working directory."""
    return Path(path).read_text(encoding="utf-8")
