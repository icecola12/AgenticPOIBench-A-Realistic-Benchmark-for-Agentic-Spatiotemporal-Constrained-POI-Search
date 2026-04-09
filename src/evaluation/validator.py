"""
Load per-task verify scripts and assign a binary reward: 1 only if ground-truth set matches
recommended POI IDs and every recommended ID passes the task's verify_poi script.
"""

from __future__ import annotations

import importlib.util
import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable


def _normalized_id_set(ids: Iterable[str]) -> set[str]:
    """Strip whitespace and drop empty strings."""
    out: set[str] = set()
    for x in ids:
        if x is None:
            continue
        s = str(x).strip()
        if s:
            out.add(s)
    return out

def load_verify_poi(verify_scripts_dir: Path, task_id: int) -> Callable[..., Any]:
    """Import verify_scripts/<task_id>.py and return its verify_poi callable."""
    tid = int(task_id)
    script_path = (verify_scripts_dir / f"{tid}.py").resolve()
    if not script_path.is_file():
        raise FileNotFoundError(f"Verify script not found for task {tid}: {script_path}")
    module_name = f"_benchmark_verify_task_{tid}"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module spec from {script_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fn = getattr(mod, "verify_poi", None)
    if not callable(fn):
        raise AttributeError(f"{script_path} must define a callable verify_poi")
    return fn


def _call_verify_for_poi(
    verify_poi: Callable[..., Any],
    poi_id: str,
    user_location: str | None,
) -> tuple[bool, str | None]:
    """
    Invoke verify_poi with target_poi_id; pass user_location when the signature accepts it.
    Returns (passed, error_message_or_none).
    """
    kwargs: dict[str, Any] = {"target_poi_id": poi_id}
    try:
        sig = inspect.signature(verify_poi)
        if user_location and "user_location" in sig.parameters:
            kwargs["user_location"] = user_location
        return bool(verify_poi(**kwargs)), None
    except Exception as e:  # noqa: BLE001 — surface script failures in the report
        return False, str(e)


@dataclass(frozen=True)
class ValidationReport:
    """Outcome of programmatic checks for one task run."""

    reward: int
    ground_truth_set_match: bool
    all_verify_scripts_passed: bool
    recommended_poi_ids: tuple[str, ...]
    ground_truth_poi_ids: tuple[str, ...]
    per_poi_passed: dict[str, bool] = field(default_factory=dict)
    per_poi_errors: dict[str, str] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        """Flat dict for merging under an evaluation section in JSON artifacts."""
        return {
            "ground_truth_set_match": self.ground_truth_set_match,
            "all_verify_scripts_passed": self.all_verify_scripts_passed,
            "recommended_poi_ids": list(self.recommended_poi_ids),
            "ground_truth_poi_ids": list(self.ground_truth_poi_ids),
            "per_poi_passed": dict(self.per_poi_passed),
            "per_poi_errors": dict(self.per_poi_errors),
        }


def run_validation_and_reward(
    *,
    recommended_poi_ids: Iterable[str],
    ground_truth_all_poi: Iterable[str],
    task_id: int,
    verify_scripts_dir: Path,
    user_location: str | None = None,
) -> ValidationReport:
    """
    Reward is 1 iff recommended IDs equal ground truth as a set and verify_poi returns True
    for every distinct recommended POI ID (same task-level script, different target_poi_id).
    """
    rec_set = _normalized_id_set(recommended_poi_ids)
    gt_set = _normalized_id_set(ground_truth_all_poi)
    ground_truth_set_match = rec_set == gt_set

    verify_fn = load_verify_poi(verify_scripts_dir, task_id)
    per_poi_passed: dict[str, bool] = {}
    per_poi_errors: dict[str, str] = {}

    if not rec_set:
        all_ok = False
    else:
        all_ok = True
        for pid in sorted(rec_set):
            passed, err = _call_verify_for_poi(verify_fn, pid, user_location)
            per_poi_passed[pid] = passed
            if err:
                per_poi_errors[pid] = err
            if not passed:
                all_ok = False

    reward = 1 if (ground_truth_set_match and all_ok) else 0
    return ValidationReport(
        reward=reward,
        ground_truth_set_match=ground_truth_set_match,
        all_verify_scripts_passed=all_ok,
        recommended_poi_ids=tuple(sorted(rec_set)),
        ground_truth_poi_ids=tuple(sorted(gt_set)),
        per_poi_passed=per_poi_passed,
        per_poi_errors=per_poi_errors,
    )


def merge_validation_into_evaluation(
    evaluation_block: dict[str, Any] | None,
    report: ValidationReport,
    *,
    ground_truth_all_poi: list[str],
    recommended_order: list[str] | None = None,
) -> dict[str, Any]:
    """
    Merge programmatic validation into the evaluation object (benchmark JSON shape).

    Adds verify_results, all_poi, Achievement Rate, and Robotness; preserves judge_agent and metrics.
    Does not persist duplicate scalar reward fields; Robotness encodes full-task success (1 iff
    recommended set matches ground truth and all verify scripts pass).

    Achievement Rate (agent.md 4.3): 1 iff every recommended POI passes the verify script
    (minimum pass; does not require ground-truth set match).
    """
    base: dict[str, Any] = dict(evaluation_block) if isinstance(evaluation_block, dict) else {}
    order = (
        list(recommended_order)
        if recommended_order is not None
        else list(report.recommended_poi_ids)
    )
    verify_results = [{"poi_id": pid, "passed": bool(report.per_poi_passed.get(pid, False))} for pid in order]
    base["verify_results"] = verify_results
    base.pop("reward", None)
    base.pop("reward_1", None)
    base["all_poi"] = list(ground_truth_all_poi)
    achievement_rate = 1 if report.all_verify_scripts_passed else 0
    base["Achievement Rate"] = achievement_rate
    base["Robotness"] = 1 if report.reward == 1 else 0
    return base


def run_validation_and_reward_safe(
    *,
    recommended_poi_ids: Iterable[str],
    ground_truth_all_poi: Iterable[str],
    task_id: int,
    verify_scripts_dir: Path,
    user_location: str | None = None,
) -> ValidationReport:
    """
    Same as run_validation_and_reward but returns a zero-reward report when the verify script is missing.
    """
    try:
        return run_validation_and_reward(
            recommended_poi_ids=recommended_poi_ids,
            ground_truth_all_poi=ground_truth_all_poi,
            task_id=task_id,
            verify_scripts_dir=verify_scripts_dir,
            user_location=user_location,
        )
    except FileNotFoundError:
        rec_set = _normalized_id_set(recommended_poi_ids)
        gt_set = _normalized_id_set(ground_truth_all_poi)
        return ValidationReport(
            reward=0,
            ground_truth_set_match=rec_set == gt_set,
            all_verify_scripts_passed=False,
            recommended_poi_ids=tuple(sorted(rec_set)),
            ground_truth_poi_ids=tuple(sorted(gt_set)),
            per_poi_passed={},
            per_poi_errors={"_verify_script": "verify script not found for task"},
        )
