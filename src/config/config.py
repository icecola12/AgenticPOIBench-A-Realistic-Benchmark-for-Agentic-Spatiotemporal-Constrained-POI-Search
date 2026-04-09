

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field


def _default_project_root() -> Path:
    # src/config/config.py -> repository root
    return Path(__file__).resolve().parent.parent.parent


def _default_config_path() -> Path:
    return _default_project_root() / "src" / "config" / "config.yaml"


class PathsConfig(BaseModel):
    eval_json: str
    prompt_yaml: str
    verify_scripts_dir: str
    output_dir: str


class EnvNames(BaseModel):
    """Environment variable names (from YAML so deploys can rename without code changes)."""

    amap_key_env: str
    llm_key_env: str
    llm_api_base_env: str


class LLMConfig(BaseModel):
    user_model: str
    agent_model: str
    extract_model: str
    api_base: str
    max_concurrent_llm: int = Field(ge=1)
    temperature: float
    max_agent_tool_rounds: int = Field(ge=1)


class MCPConfig(BaseModel):
    max_concurrent_mcp: int = Field(ge=1)


class DialogConfig(BaseModel):
    max_turns: int = Field(ge=1)
    stop_token: str


class RunsConfig(BaseModel):
    num_repeats: int = Field(ge=1)
    run_name: str


class AppSettings(BaseModel):
    paths: PathsConfig
    env: EnvNames
    llm: LLMConfig
    mcp: MCPConfig
    dialog: DialogConfig
    runs: RunsConfig


def load_yaml_dict(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"Config file must be a YAML mapping: {path}")
    return data


def load_app_settings(
    config_path: Optional[Path] = None,
    project_root: Optional[Path] = None,
) -> tuple[AppSettings, Path]:
    """
    Parse config.yaml into AppSettings.
    project_root resolves relative paths under paths; defaults to this repository root.
    """
    root = (project_root or _default_project_root()).resolve()
    path = (config_path or _default_config_path()).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")
    raw = load_yaml_dict(path)
    return AppSettings.model_validate(raw), root


def _require_env(name: str) -> str:
    v = os.environ.get(name)
    if v is None or not str(v).strip():
        raise RuntimeError(
            f"Missing or empty environment variable {name!r}. Set it in your shell or .env before running."
        )
    return str(v).strip()


def _optional_env(name: str) -> Optional[str]:
    v = os.environ.get(name)
    if v is None or not str(v).strip():
        return None
    return str(v).strip()


@dataclass(frozen=True)
class ResolvedSecrets:
    """Secrets from environment variables plus optional overrides."""

    amap_api_key: str
    llm_api_key: str
    llm_api_base: Optional[str]


def resolve_secrets(settings: AppSettings) -> ResolvedSecrets:
    """Read secrets using variable names from config.yaml env.*."""
    e = settings.env
    amap = _require_env(e.amap_key_env)
    llm_key = _require_env(e.llm_key_env)
    base = _optional_env(e.llm_api_base_env)
    return ResolvedSecrets(amap_api_key=amap, llm_api_key=llm_key, llm_api_base=base)


def resolve_path(project_root: Path, p: str) -> Path:
    """Resolve a paths.* entry: relative paths are relative to the repository root."""
    path = Path(p)
    if path.is_absolute():
        return path
    return (project_root / path).resolve()


@dataclass(frozen=True)
class ResolvedConfig:
    """Runtime config: YAML settings, project root, secrets, and common absolute paths."""

    settings: AppSettings
    project_root: Path
    secrets: ResolvedSecrets
    eval_json: Path
    prompt_yaml: Path
    verify_scripts_dir: Path
    output_dir: Path

    @property
    def llm_api_base_effective(self) -> str:
        """Prefer LLM_API_BASE from env (name in config.yaml env.llm_api_base_env), else llm.api_base from YAML."""
        if self.secrets.llm_api_base:
            return self.secrets.llm_api_base
        return self.settings.llm.api_base


def load_resolved_config(
    config_path: Optional[Path] = None,
    project_root: Optional[Path] = None,
) -> ResolvedConfig:
    """Load YAML, validate structure, and read secrets from the environment."""
    settings, root = load_app_settings(config_path=config_path, project_root=project_root)
    secrets = resolve_secrets(settings)
    p = settings.paths
    return ResolvedConfig(
        settings=settings,
        project_root=root,
        secrets=secrets,
        eval_json=resolve_path(root, p.eval_json),
        prompt_yaml=resolve_path(root, p.prompt_yaml),
        verify_scripts_dir=resolve_path(root, p.verify_scripts_dir),
        output_dir=resolve_path(root, p.output_dir),
    )


def resolved_config_with_llm_overrides(
    base: ResolvedConfig,
    *,
    user_model: Optional[str] = None,
    agent_model: Optional[str] = None,
    extract_model: Optional[str] = None,
) -> ResolvedConfig:
    """Return a new ResolvedConfig with selected llm.*_model fields replaced (YAML on disk unchanged)."""
    llm = base.settings.llm
    updates: dict[str, Any] = {}
    if user_model is not None and str(user_model).strip():
        updates["user_model"] = str(user_model).strip()
    if agent_model is not None and str(agent_model).strip():
        updates["agent_model"] = str(agent_model).strip()
    if extract_model is not None and str(extract_model).strip():
        updates["extract_model"] = str(extract_model).strip()
    if not updates:
        return base
    new_llm = llm.model_copy(update=updates)
    new_settings = base.settings.model_copy(update={"llm": new_llm})
    return ResolvedConfig(
        settings=new_settings,
        project_root=base.project_root,
        secrets=base.secrets,
        eval_json=base.eval_json,
        prompt_yaml=base.prompt_yaml,
        verify_scripts_dir=base.verify_scripts_dir,
        output_dir=base.output_dir,
    )


@lru_cache(maxsize=1)
def get_resolved_config_cached(
    config_path_str: Optional[str] = None,
    project_root_str: Optional[str] = None,
) -> ResolvedConfig:
    """Process-wide singleton cache (paths passed as strings for lru_cache keys)."""
    cp = Path(config_path_str) if config_path_str else None
    pr = Path(project_root_str) if project_root_str else None
    return load_resolved_config(config_path=cp, project_root=pr)
