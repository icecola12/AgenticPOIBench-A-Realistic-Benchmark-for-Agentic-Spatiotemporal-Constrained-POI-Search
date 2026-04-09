"""
Run one or more dialogues through the LangGraph loop and write dialogue logs + task JSON.
After each run, writes summary.json under the artifact directory with aggregate metrics.

Default output: results/exp_<agent_model>_<utc_timestamp>/ (task JSON + summary.json) and
results/exp_.../log/ for dialogue_*.json. Override with --artifact-dir.

Usage from repository root::

    export AMAP_MCP_KEY=...
    export LITELLM_API_KEY=...
    uv run python scripts/run_dialogue_once.py
    uv run python scripts/run_dialogue_once.py --eval-index 0
    uv run python scripts/run_dialogue_once.py --agent-model openai/gpt-4o
    uv run python scripts/run_dialogue_once.py --artifact-dir /path/to/custom_out

PYTHONPATH is adjusted automatically so imports resolve without manual export.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path


def _ensure_src_on_path() -> Path:
    root = Path(__file__).resolve().parent.parent
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    return root


def _parse_args() -> argparse.Namespace:
    _ensure_src_on_path()
    from cli_batch import add_batch_ui_arguments

    epilog = (
        "Eval indices are 0-based (same as --eval-index). "
        "Example: 1-based tasks 2 through 10 => --start-index 1 --end-index 9. "
        "Omit --artifact-dir to create a fresh results/exp_<model>_<timestamp>/ directory per invocation."
    )
    p = argparse.ArgumentParser(
        description="Run dialogue(s) for one eval index or an inclusive index range.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    add_batch_ui_arguments(p)
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
        help="Inclusive range start (0-based); requires --end-index",
    )
    p.add_argument(
        "--end-index",
        type=int,
        default=None,
        metavar="E",
        help="Inclusive range end (0-based); requires --start-index",
    )
    p.add_argument(
        "--artifact-dir",
        type=Path,
        default=None,
        help="Explicit directory for task_*.json (optional; default is auto results/exp_<model>_<timestamp>/)",
    )
    p.add_argument(
        "--agent-model",
        type=str,
        default=None,
        metavar="ID",
        help="Override config llm.agent_model for this run (LiteLLM model id)",
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
    return p.parse_args()


async def main() -> None:
    args = _parse_args()
    if (args.start_index is None) ^ (args.end_index is None):
        raise SystemExit("Both --start-index and --end-index are required for a range (or omit both for --eval-index).")

    root = _ensure_src_on_path()
    from cli_batch import configure_run_logging, iterate_tasks_with_progress, should_show_task_progress
    from config import load_resolved_config, resolved_config_with_llm_overrides
    from data import load_eval_json_from_config_eval_path, select_eval_records_for_cli_indices
    from experiment_paths import make_experiment_run_dir
    from orchestration.graph import run_dialogue_loop
    from orchestration.run_summary import write_batch_run_summary_json

    configure_run_logging(verbose=args.verbose, quiet=args.quiet)

    base_cfg = load_resolved_config(project_root=root)
    r = resolved_config_with_llm_overrides(
        base_cfg,
        user_model=args.user_model,
        agent_model=args.agent_model,
        extract_model=args.extract_model,
    )
    effective_agent = r.settings.llm.agent_model

    if args.artifact_dir is not None:
        art_dir = args.artifact_dir if args.artifact_dir.is_absolute() else (root / args.artifact_dir).resolve()
        art_dir.mkdir(parents=True, exist_ok=True)
    else:
        art_dir = make_experiment_run_dir(root, effective_agent)
    log_dir = art_dir / "log"

    recs = load_eval_json_from_config_eval_path(root, r.settings.paths.eval_json)
    selected = select_eval_records_for_cli_indices(
        recs,
        eval_index=args.eval_index,
        start_index=args.start_index,
        end_index_inclusive=args.end_index,
    )
    batch_range = args.start_index is not None and args.end_index is not None
    show_bar = should_show_task_progress(
        no_progress=args.no_progress,
        num_tasks=len(selected),
        batch_range=batch_range,
    )
    batch_results: list[tuple[int, Path, dict]] = []
    for record in iterate_tasks_with_progress(selected, show_progress=show_bar, desc="Dialogue"):
        out = await run_dialogue_loop(
            r,
            record,
            log_dir=log_dir,
            artifact_dir=art_dir,
            run_label="manual",
        )
        batch_results.append((int(record.id), out.artifact_path, out.evaluation))
    summary_path = write_batch_run_summary_json(
        command="dialogue",
        artifact_dir=art_dir,
        agent_model_from_config=base_cfg.settings.llm.agent_model,
        agent_model_cli_override=args.agent_model,
        results=batch_results,
    )
    print(
        f"Done ({len(selected)} task(s)). Dialogue logs: {log_dir}/ "
        f"Artifacts and summary: {art_dir}/"
    )
    if summary_path is not None:
        print(f"Run summary: {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
