"""Read project settings once; all other parts use the shared settings object."""
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseModel):
    """Environment-backed configuration; relative paths use the project folder."""

    active_template: str = Field(default="payments", min_length=1)
    templates_dir: Path = Path("part1_templates/templates")
    llm_provider: Literal["fake", "ollama", "anthropic", "openai"] = "fake"
    llm_model: str = "qwen2.5:7b"
    ollama_base_url: str = "http://localhost:11434"
    anthropic_api_key: str = Field(default="", repr=False)
    openai_api_key: str = Field(default="", repr=False)
    chroma_dir: Path = Path("runtime/chroma")
    app_db: Path = Path("runtime/app.db")
    llm_timeout_seconds: int = Field(default=120, gt=0)
    llm_max_retries: int = Field(default=1, ge=0)


def _load_settings(project_root: Path = PROJECT_ROOT) -> Settings:
    load_dotenv(project_root / ".env", override=False)
    values = {name: os.environ[name.upper()] for name in Settings.model_fields
              if os.environ.get(name.upper())}
    loaded = Settings.model_validate(values)
    for name in ("templates_dir", "chroma_dir", "app_db"):
        path = getattr(loaded, name)
        setattr(loaded, name, (project_root / path).resolve())
    (project_root / "runtime").mkdir(parents=True, exist_ok=True)
    return loaded


settings = _load_settings()
