"""
Timestamped experiment directories under <project_root>/results/exp_<model_slug>_<utc_time>/.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def sanitize_model_for_path(model_id: str) -> str:
    """Map a LiteLLM-style model id to a single path segment (no slashes or OS-forbidden chars)."""
    s = (model_id or "").strip()
    s = re.sub(r'[/\\:*?"<>|\s]+', "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return (s[:120] if s else "model")


def make_experiment_run_dir(project_root: Path, effective_agent_model: str) -> Path:
    """
    Create and return results/exp_<slug>_<timestamp>/ (UTC). Adds a short suffix if the path exists.
    """
    base = (project_root / "results").resolve()
    base.mkdir(parents=True, exist_ok=True)
    slug = sanitize_model_for_path(effective_agent_model)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"exp_{slug}_{ts}"
    path = base / name
    if path.exists():
        name = f"exp_{slug}_{ts}_{uuid4().hex[:8]}"
        path = base / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def find_latest_results_experiment_dir(project_root: Path) -> Path | None:
    """Newest results/exp_* directory by mtime, or None if missing."""
    results = (project_root / "results").resolve()
    if not results.is_dir():
        return None
    candidates = [p for p in results.iterdir() if p.is_dir() and p.name.startswith("exp_")]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def resolve_artifact_dir_for_cli(project_root: Path, artifact_dir: Path | None) -> Path:
    """
    Resolve batch/single default artifact root: explicit --artifact-dir, else newest results/exp_*.
    """
    if artifact_dir is not None:
        p = artifact_dir if artifact_dir.is_absolute() else (project_root / artifact_dir).resolve()
        if not p.is_dir():
            raise FileNotFoundError(f"Artifact directory not found: {p}")
        return p
    latest = find_latest_results_experiment_dir(project_root)
    if latest is None:
        raise FileNotFoundError(
            "No results/exp_* directory found; run dialogue first or pass --artifact-dir "
            f"(project_root={project_root})."
        )
    return latest
