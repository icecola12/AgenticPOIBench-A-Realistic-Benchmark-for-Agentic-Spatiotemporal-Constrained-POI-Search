"""
Run the full dialogue + evaluation pipeline k times on one or more eval samples (Pass@k).

Default artifacts and logs: one shared results/exp_<agent_model>_<timestamp>/ per CLI invocation
(with a log/ subdirectory). Override with --artifact-dir.

Usage from repository root::

    export AMAP_MCP_KEY=...
    export LITELLM_API_KEY=...
    uv run python scripts/run_pass_at_k.py
    uv run python scripts/run_pass_at_k.py --k 2 --eval-index 0
    uv run python scripts/run_pass_at_k.py --k 2 --agent-model openai/gpt-4o
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def _ensure_src_on_path() -> Path:
    root = Path(__file__).resolve().parent.parent
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    return root


async def _run_one_task_report(
    resolved,
    record,
    *,
    k: int,
    mc_batches: int,
    log_dir: Path,
    artifact_dir: Path,
    run_name_prefix: str,
) -> dict:
    from orchestration import (
        run_dialogue_pass_at_k,
        run_dialogue_pass_at_k_monte_carlo,
    )

    if mc_batches > 1:
        return await run_dialogue_pass_at_k_monte_carlo(
            resolved,
            record,
            k,
            monte_carlo_batches=mc_batches,
            log_dir=log_dir,
            artifact_dir=artifact_dir,
            run_label_prefix=f"{run_name_prefix}_",
        )
    return await run_dialogue_pass_at_k(
        resolved,
        record,
        k,
        log_dir=log_dir,
        artifact_dir=artifact_dir,
        run_label_prefix=f"{run_name_prefix}_",
    )


async def _async_main(
    *,
    k: int,
    eval_index: int,
    start_index: int | None,
    end_index: int | None,
    mc_batches: int,
    report_path: Path | None,
    no_progress: bool,
    artifact_dir: Path,
    log_dir: Path,
    resolved,
) -> None:
    root = _ensure_src_on_path()
    from data import load_eval_json_from_config_eval_path, select_eval_records_for_cli_indices

    recs = load_eval_json_from_config_eval_path(root, resolved.settings.paths.eval_json)
    selected = select_eval_records_for_cli_indices(
        recs,
        eval_index=eval_index,
        start_index=start_index,
        end_index_inclusive=end_index,
    )

    base_prefix = (resolved.settings.runs.run_name.strip() or "run").rstrip("_")

    from cli_batch import iterate_tasks_with_progress, should_show_task_progress

    batch_range = start_index is not None and end_index is not None
    show_bar = should_show_task_progress(
        no_progress=no_progress,
        num_tasks=len(selected),
        batch_range=batch_range,
    )
    reports: list[dict] = []
    for record in iterate_tasks_with_progress(selected, show_progress=show_bar, desc="Pass@k"):
        tid = int(record.id)
        report = await _run_one_task_report(
            resolved,
            record,
            k=k,
            mc_batches=mc_batches,
            log_dir=log_dir,
            artifact_dir=artifact_dir,
            run_name_prefix=f"{base_prefix}_task{tid}",
        )
        report["written_at_utc"] = datetime.now(timezone.utc).isoformat()
        reports.append(report)

    if len(reports) == 1:
        out_payload: dict = reports[0]
    else:
        out_payload = {
            "eval_batch": {
                "start_index": start_index,
                "end_index_inclusive": end_index,
                "num_tasks": len(reports),
            },
            "tasks": reports,
        }

    print(json.dumps(out_payload, ensure_ascii=False, indent=2))

    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(out_payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    _ensure_src_on_path()
    from cli_batch import add_batch_ui_arguments, configure_run_logging

    epilog = (
        "Eval indices are 0-based. Example: 1-based tasks 2–10 => --start-index 1 --end-index 9. "
        "Omit --artifact-dir to create a fresh results/exp_<model>_<timestamp>/ directory per invocation."
    )
    p = argparse.ArgumentParser(
        description="Run Pass@k: k full pipeline repeats per eval task (optional index range).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    add_batch_ui_arguments(p)
    p.add_argument(
        "--k",
        type=int,
        default=None,
        help="Number of independent runs (default: config runs.num_repeats)",
    )
    p.add_argument(
        "--eval-index",
        type=int,
        default=0,
        metavar="I",
        help="Single eval sample index (default: 0). Ignored when --start-index/--end-index are set.",
    )
    p.add_argument(
        "--start-index",
        type=int,
        default=None,
        metavar="S",
        help="Inclusive batch start (0-based); requires --end-index",
    )
    p.add_argument(
        "--end-index",
        type=int,
        default=None,
        metavar="E",
        help="Inclusive batch end (0-based); requires --start-index",
    )
    p.add_argument(
        "--artifact-dir",
        type=Path,
        default=None,
        help="Explicit directory for task JSON + logs subdirectory (default: auto results/exp_<model>_<timestamp>/)",
    )
    p.add_argument(
        "--agent-model",
        type=str,
        default=None,
        metavar="ID",
        help="Override config llm.agent_model for this run",
    )
    p.add_argument(
        "--user-model",
        type=str,
        default=None,
        metavar="ID",
        help="Override config llm.user_model for this run",
    )
    p.add_argument(
        "--extract-model",
        type=str,
        default=None,
        metavar="ID",
        help="Override config llm.extract_model for this run",
    )
    p.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional path to write the JSON report (e.g. results/exp_.../pass_at_k_report.json)",
    )
    p.add_argument(
        "--mc-batches",
        type=int,
        default=1,
        metavar="N",
        help=(
            "Repeat the full k-run Pass@k block N times; report empirical_probability_all_k_succeed "
            "as the fraction of blocks where all k runs succeeded (default: 1)"
        ),
    )
    args = p.parse_args()
    configure_run_logging(verbose=args.verbose, quiet=args.quiet)
    if (args.start_index is None) ^ (args.end_index is None):
        raise SystemExit("Both --start-index and --end-index are required for a range (or omit both for --eval-index).")

    root = _ensure_src_on_path()
    from config import load_resolved_config, resolved_config_with_llm_overrides
    from experiment_paths import make_experiment_run_dir

    base_cfg = load_resolved_config(project_root=root)
    resolved = resolved_config_with_llm_overrides(
        base_cfg,
        user_model=args.user_model,
        agent_model=args.agent_model,
        extract_model=args.extract_model,
    )
    k = args.k if args.k is not None else int(resolved.settings.runs.num_repeats)

    rp = args.report
    if rp is not None and not rp.is_absolute():
        rp = Path.cwd() / rp

    if args.mc_batches < 1:
        raise SystemExit("--mc-batches must be >= 1")

    effective_agent = resolved.settings.llm.agent_model
    if args.artifact_dir is not None:
        art_dir = args.artifact_dir if args.artifact_dir.is_absolute() else (root / args.artifact_dir).resolve()
        art_dir.mkdir(parents=True, exist_ok=True)
    else:
        art_dir = make_experiment_run_dir(root, effective_agent)
    log_dir = art_dir / "log"

    asyncio.run(
        _async_main(
            k=k,
            eval_index=args.eval_index,
            start_index=args.start_index,
            end_index=args.end_index,
            mc_batches=args.mc_batches,
            report_path=rp,
            no_progress=args.no_progress,
            artifact_dir=art_dir,
            log_dir=log_dir,
            resolved=resolved,
        )
    )


if __name__ == "__main__":
    main()
