"""
Compute evaluation (judge + verify scripts + reward) for saved task JSON file(s).

By default merges evaluation into each JSON file (other top-level keys unchanged) and prints
the evaluation object to stdout. Use --dry-run to print only without writing.

Default artifact directory: newest results/exp_* from a prior dialogue run, unless --artifact-dir
or an explicit --dialogue path is given.

Usage from repository root::

    export AMAP_MCP_KEY=...
    export LITELLM_API_KEY=...
    uv run python scripts/run_evaluate_once.py
    uv run python scripts/run_evaluate_once.py --dialogue results/exp_.../task_1_manual.json
    uv run python scripts/run_evaluate_once.py --start-index 0 --end-index 2
    uv run python scripts/run_evaluate_once.py --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path


def _ensure_src_on_path() -> Path:
    root = Path(__file__).resolve().parent.parent
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    return root


async def _evaluate_one_path(
    root: Path,
    dialogue_path: Path,
    *,
    dry_run: bool,
    extract_model: str | None,
) -> dict:
    from config import load_resolved_config, resolved_config_with_llm_overrides
    from data import load_dialogue_artifact_json, load_eval_json_from_config_eval_path
    from evaluation import build_evaluation_for_saved_artifact

    base = load_resolved_config(project_root=root)
    resolved = resolved_config_with_llm_overrides(base, extract_model=extract_model)
    recs = load_eval_json_from_config_eval_path(root, resolved.settings.paths.eval_json)
    doc = load_dialogue_artifact_json(dialogue_path)
    task = doc.get("task")
    tid = None
    if isinstance(task, dict):
        tid = task.get("id")
    record = next((r for r in recs if str(r.id) == str(tid)), None)
    if record is None:
        raise SystemExit(f"No eval record with id matching dialogue task id {tid!r}")

    evaluation = await build_evaluation_for_saved_artifact(resolved, record, doc)

    if not dry_run:
        merged_doc = dict(doc)
        merged_doc["evaluation"] = evaluation
        dialogue_path.write_text(json.dumps(merged_doc, ensure_ascii=False, indent=2), encoding="utf-8")

    return evaluation


async def _async_main(
    *,
    dialogue_path: Path | None,
    start_index: int | None,
    end_index: int | None,
    artifact_dir: Path,
    run_label: str | None,
    dry_run: bool,
    no_progress: bool,
    extract_model: str | None,
    base_agent_model_for_summary: str,
) -> None:
    root = _ensure_src_on_path()
    from config import load_resolved_config
    from data import load_eval_json_from_config_eval_path, select_eval_records_for_cli_indices
    from persistence import find_task_artifact_json

    cfg = load_resolved_config(project_root=root)
    recs = load_eval_json_from_config_eval_path(root, cfg.settings.paths.eval_json)
    batch_range = start_index is not None and end_index is not None

    if batch_range:
        selected = select_eval_records_for_cli_indices(
            recs,
            eval_index=0,
            start_index=start_index,
            end_index_inclusive=end_index,
        )
        art_dir = artifact_dir
        from cli_batch import iterate_tasks_with_progress, should_show_task_progress
        from orchestration.run_summary import write_batch_run_summary_json

        batch_out: list[dict] = []
        batch_results: list[tuple[int, Path, dict]] = []
        show_bar = should_show_task_progress(
            no_progress=no_progress,
            num_tasks=len(selected),
            batch_range=True,
        )
        for record in iterate_tasks_with_progress(selected, show_progress=show_bar, desc="Evaluate"):
            path = find_task_artifact_json(art_dir, int(record.id), preferred_label=run_label)
            ev = await _evaluate_one_path(root, path, dry_run=dry_run, extract_model=extract_model)
            one = dict(ev)
            one["dialogue_path"] = str(path)
            one["eval_task_id"] = int(record.id)
            batch_out.append(one)
            batch_results.append((int(record.id), path, ev))
        print(json.dumps(batch_out, ensure_ascii=False, indent=2))
        summary_path = write_batch_run_summary_json(
            command="evaluate",
            artifact_dir=art_dir,
            agent_model_from_config=base_agent_model_for_summary,
            agent_model_cli_override=None,
            results=batch_results,
        )
        if summary_path is not None:
            print(f"Run summary: {summary_path}", file=sys.stderr)
        return

    if dialogue_path is None:
        raise SystemExit("Single-file mode requires --dialogue")
    path = dialogue_path if dialogue_path.is_absolute() else (Path.cwd() / dialogue_path).resolve()
    evaluation = await _evaluate_one_path(root, path, dry_run=dry_run, extract_model=extract_model)
    print(json.dumps(evaluation, ensure_ascii=False, indent=2))


def main() -> None:
    _ensure_src_on_path()
    from cli_batch import add_batch_ui_arguments, configure_run_logging

    epilog = (
        "Eval indices are 0-based. Example: 1-based tasks 2–10 => --start-index 1 --end-index 9. "
        "Without --artifact-dir, the newest results/exp_* directory is used (after a dialogue run)."
    )
    p = argparse.ArgumentParser(
        description="Run full evaluation on one saved task JSON or on each task in an eval index range.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    add_batch_ui_arguments(p)
    p.add_argument(
        "--dialogue",
        type=Path,
        default=None,
        help="Path to task_*.json (single-file mode; if omitted, uses task 1 under resolved artifact dir)",
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
        help="Directory containing task_*.json (default: newest results/exp_* directory)",
    )
    p.add_argument(
        "--run-label",
        type=str,
        default="manual",
        help="Preferred filename suffix for task_<id>_<label>.json when batching (default: manual)",
    )
    p.add_argument(
        "--extract-model",
        type=str,
        default=None,
        metavar="ID",
        help="Override config llm.extract_model for judge/extractor in this run",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print evaluation to stdout; do not modify JSON file(s)",
    )
    args = p.parse_args()
    configure_run_logging(verbose=args.verbose, quiet=args.quiet)
    if (args.start_index is None) ^ (args.end_index is None):
        raise SystemExit("Both --start-index and --end-index are required for batch mode (or omit both for single file).")

    root = _ensure_src_on_path()
    from config import load_resolved_config
    from experiment_paths import resolve_artifact_dir_for_cli
    from persistence import find_task_artifact_json

    base_cfg = load_resolved_config(project_root=root)
    batch_range = args.start_index is not None and args.end_index is not None

    dialogue: Path | None = args.dialogue
    art_dir_resolved: Path | None = None
    if batch_range or args.dialogue is None:
        try:
            art_dir_resolved = resolve_artifact_dir_for_cli(root, args.artifact_dir)
        except FileNotFoundError as e:
            raise SystemExit(str(e)) from e

    if batch_range:
        pass
    elif args.dialogue is None:
        assert art_dir_resolved is not None
        dialogue = find_task_artifact_json(art_dir_resolved, 1, preferred_label=args.run_label)
    elif dialogue is not None:
        dialogue = dialogue if dialogue.is_absolute() else (Path.cwd() / dialogue)

    asyncio.run(
        _async_main(
            dialogue_path=dialogue.resolve() if dialogue is not None else None,
            start_index=args.start_index,
            end_index=args.end_index,
            artifact_dir=art_dir_resolved if art_dir_resolved is not None else Path(),
            run_label=args.run_label,
            dry_run=args.dry_run,
            no_progress=args.no_progress,
            extract_model=args.extract_model,
            base_agent_model_for_summary=base_cfg.settings.llm.agent_model,
        )
    )


if __name__ == "__main__":
    main()
