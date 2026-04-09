"""
Write summary.json next to task artifacts after multi-task dialogue or evaluate batch runs.

Aggregates per-task evaluation scalars (achievement, robust completion / Robotness, steps, tool calls)
without embedding full judge narratives in the per-task section.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mean_numeric(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _collect_numeric_values(evaluations: list[dict[str, Any]], key: str) -> list[float]:
    out: list[float] = []
    for ev in evaluations:
        f = _coerce_float(ev.get(key))
        if f is not None:
            out.append(f)
    return out


def build_per_task_summary_row(
    task_id: int,
    artifact_path: Path,
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    """High-signal per-task metrics only (no judge_agent blob)."""
    rec = evaluation.get("recommended_poi_ids")
    n_rec = len(rec) if isinstance(rec, list) else 0
    row: dict[str, Any] = {
        "task_id": int(task_id),
        "artifact_path": str(Path(artifact_path).resolve()),
        "recommended_poi_ids_count": n_rec,
    }
    for key in ("Achievement Rate", "Robotness", "step", "tool_calls_total", "termination_reason"):
        if key in evaluation:
            row[key] = evaluation[key]
    return row


def build_aggregate_means(evaluations: list[dict[str, Any]]) -> dict[str, float]:
    """
    Means over tasks. Robust Completion Rate is the mean of per-task Robotness (full-task success).
    """
    achievement = _mean_numeric(_collect_numeric_values(evaluations, "Achievement Rate"))
    robust = _mean_numeric(_collect_numeric_values(evaluations, "Robotness"))
    step_mean = _mean_numeric(_collect_numeric_values(evaluations, "step"))
    tool_mean = _mean_numeric(_collect_numeric_values(evaluations, "tool_calls_total"))
    return {
        "Achievement Rate": achievement,
        "Robust Completion Rate": robust,
        "evaluation.step": step_mean,
        "evaluation.tool_calls_total": tool_mean,
    }


def build_run_summary_payload(
    *,
    command: str,
    artifact_dir: Path,
    agent_model_from_config: str,
    agent_model_cli_override: str | None,
    results: list[tuple[int, Path, dict[str, Any]]],
) -> dict[str, Any]:
    """Assemble the on-disk summary document (one entry per completed task)."""
    evaluations = [ev for _, _, ev in results]
    tasks = [build_per_task_summary_row(tid, path, ev) for tid, path, ev in results]
    return {
        "written_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "artifact_dir": str(Path(artifact_dir).resolve()),
        "task_count": len(results),
        "agent_model": {
            "from_config": agent_model_from_config,
            "cli_override": agent_model_cli_override,
        },
        "aggregate_means": build_aggregate_means(evaluations),
        "tasks": tasks,
    }


def write_batch_run_summary_json(
    *,
    command: str,
    artifact_dir: Path,
    agent_model_from_config: str,
    agent_model_cli_override: str | None = None,
    results: list[tuple[int, Path, dict[str, Any]]],
) -> Path | None:
    """
    Persist summary.json under artifact_dir. Returns the file path, or None if results is empty.
    """
    if not results:
        return None
    out_dir = Path(artifact_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_run_summary_payload(
        command=command,
        artifact_dir=out_dir,
        agent_model_from_config=agent_model_from_config,
        agent_model_cli_override=agent_model_cli_override,
        results=results,
    )
    path = out_dir / "summary.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
