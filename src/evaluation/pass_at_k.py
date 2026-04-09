"""
Pass@k-style robustness: k independent runs, binary success per run, joint success if all k pass.

Used to aggregate rewards from repeated full pipeline executions on the same task.
"""

from __future__ import annotations

from typing import Any, Sequence


def reward_success(reward: int | None, *, success_value: int = 1) -> bool:
    """True if the evaluation reward indicates a fully successful run."""
    return int(reward) == success_value if reward is not None else False


def summarize_pass_at_k_from_rewards(
    rewards: Sequence[int | None],
    *,
    success_value: int = 1,
) -> dict[str, Any]:
    """
    Build a JSON-serializable report for k independent runs.

    - per_run_success: success flag for each run (same order as rewards).
    - all_runs_succeeded: True iff every run succeeded (robustness criterion for this batch).
    - joint_success_probability: 1.0 if all k runs succeeded in this batch, else 0.0 (point estimate).
    - batch_robustness_score: same as joint_success_probability (alias for dashboards).
    - independent_joint_estimate: if each run were i.i.d. with p = empirical success rate,
      p^k is a plug-in diagnostic for joint success under independence (not calibrated).
    """
    per_run = [reward_success(r, success_value=success_value) for r in rewards]
    k = len(per_run)
    all_ok = bool(per_run) and all(per_run)
    successes = sum(1 for x in per_run if x)
    p_hat = successes / k if k else 0.0
    joint = 1.0 if all_ok else 0.0
    return {
        "k": k,
        "per_run_success": per_run,
        "per_run_reward": [int(r) if r is not None else None for r in rewards],
        "all_runs_succeeded": all_ok,
        "joint_success_probability": joint,
        "batch_robustness_score": joint,
        "empirical_success_rate": p_hat,
        "independent_joint_estimate": (p_hat**k) if k else 1.0,
    }


def summarize_monte_carlo_pass_at_k(
    batch_all_succeeded: Sequence[bool],
) -> dict[str, Any]:
    """
    Aggregate several independent k-run batches: estimate P(all k runs succeed) as the
    fraction of batches where every run in that batch succeeded.
    """
    flags = list(batch_all_succeeded)
    n = len(flags)
    if n == 0:
        return {
            "monte_carlo_batches": 0,
            "empirical_probability_all_k_succeed": 0.0,
            "batch_all_joint_success": [],
        }
    hits = sum(1 for x in flags if x)
    return {
        "monte_carlo_batches": n,
        "empirical_probability_all_k_succeed": hits / n,
        "batch_all_joint_success": flags,
    }
