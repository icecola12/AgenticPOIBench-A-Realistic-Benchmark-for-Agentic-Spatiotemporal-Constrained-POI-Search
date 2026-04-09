"""
Run the full dialogue + evaluation pipeline k times on one eval record (Pass@k / robustness).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from config import ResolvedConfig
from data import EvalRecord
from evaluation.pass_at_k import (
    summarize_monte_carlo_pass_at_k,
    summarize_pass_at_k_from_rewards,
)
from orchestration.graph import DialogueRunResult, run_dialogue_loop


async def run_dialogue_pass_at_k(
    resolved: ResolvedConfig,
    record: EvalRecord,
    k: int,
    *,
    log_dir: Path | None = None,
    artifact_dir: Path | None = None,
    run_label_prefix: str = "run",
) -> dict[str, Any]:
    """
    Execute run_dialogue_loop k times with distinct run labels; return per-run results and summary.

    Each iteration is independent (fresh graph run). Artifacts and logs use artifact_dir and
    log_dir passed through to run_dialogue_loop (run labels include the run index).
    """
    if k < 1:
        raise ValueError("k must be >= 1")
    results: list[DialogueRunResult] = []
    for i in range(k):
        label = f"{run_label_prefix}{i}"
        out = await run_dialogue_loop(
            resolved,
            record,
            log_dir=log_dir,
            artifact_dir=artifact_dir,
            run_label=label,
        )
        results.append(out)

    def _full_success_flag(ev: dict[str, Any] | None) -> int | None:
        """1/0 from Robotness; fall back to legacy evaluation.reward for older artifacts."""
        if not isinstance(ev, dict):
            return None
        for key in ("Robotness", "reward"):
            raw = ev.get(key)
            if raw is None:
                continue
            try:
                return int(raw)
            except (TypeError, ValueError):
                continue
        return None

    rewards: list[int | None] = []
    for r in results:
        rewards.append(_full_success_flag(r.evaluation if isinstance(r.evaluation, dict) else None))

    summary = summarize_pass_at_k_from_rewards(rewards)
    achievement_rates: list[int] = []
    for r in results:
        ev = r.evaluation if isinstance(r.evaluation, dict) else {}
        ar = ev.get("Achievement Rate")
        if ar is not None:
            try:
                achievement_rates.append(int(ar))
            except (TypeError, ValueError):
                achievement_rates.append(0)
        else:
            achievement_rates.append(0)
    ar_mean = sum(achievement_rates) / len(achievement_rates) if achievement_rates else 0.0
    robotness_joint = 1 if summary.get("all_runs_succeeded") else 0
    return {
        "task_id": int(record.id),
        "runs": [
            {
                "run_index": i,
                "run_label": f"{run_label_prefix}{i}",
                "artifact_path": str(r.artifact_path),
                "reward": rewards[i],
            }
            for i, r in enumerate(results)
        ],
        "pass_at_k": summary,
        "Achievement Rate": ar_mean,
        "Robotness": robotness_joint,
    }


async def run_dialogue_pass_at_k_monte_carlo(
    resolved: ResolvedConfig,
    record: EvalRecord,
    k: int,
    *,
    monte_carlo_batches: int,
    log_dir: Path | None = None,
    artifact_dir: Path | None = None,
    run_label_prefix: str = "run",
) -> dict[str, Any]:
    """
    Repeat the full dialogue+evaluation pipeline ``monte_carlo_batches`` times; each batch
    runs ``k`` independent dialogues. Reports empirical P(all k succeed) across batches.
    """
    if monte_carlo_batches < 1:
        raise ValueError("monte_carlo_batches must be >= 1")
    batch_reports: list[dict[str, Any]] = []
    joint_flags: list[bool] = []
    for b in range(monte_carlo_batches):
        prefix = f"{run_label_prefix}b{b}_"
        one = await run_dialogue_pass_at_k(
            resolved,
            record,
            k,
            log_dir=log_dir,
            artifact_dir=artifact_dir,
            run_label_prefix=prefix,
        )
        batch_reports.append(one)
        pa = one.get("pass_at_k") if isinstance(one.get("pass_at_k"), dict) else {}
        joint_flags.append(bool(pa.get("all_runs_succeeded")))
    mc = summarize_monte_carlo_pass_at_k(joint_flags)
    ar_batch_means = [
        float(b.get("Achievement Rate", 0.0))
        for b in batch_reports
        if isinstance(b, dict)
    ]
    ar_over_batches = sum(ar_batch_means) / len(ar_batch_means) if ar_batch_means else 0.0
    return {
        "task_id": int(record.id),
        "k": k,
        "monte_carlo": mc,
        "batches": batch_reports,
        "Achievement Rate": ar_over_batches,
        "Robotness": float(mc.get("empirical_probability_all_k_succeed", 0.0)),
    }
