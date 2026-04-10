"""
Unified CLI: dispatches subcommands to existing pipeline scripts (same argv as direct script runs).

Usage from repository root::

    ./AgenticPOIBench dialogue --eval-index 0
    ./AgenticPOIBench verify --resolve-secrets
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_CLI_PROG = "AgenticPOIBench"

_COMMAND_SCRIPTS: dict[str, str] = {
    "dialogue": "run_dialogue_once.py",
    "evaluate": "run_evaluate_once.py",
    "pass_hat_k": "run_pass_at_k.py",
    "verify": "verify_env.py",
}

_INDEX_HELP = (
    "Eval indices are 0-based (aligned with --eval-index in each script). "
    "Example: 1-based tasks 2 through 10 => --start-index 1 --end-index 9."
)

_COMMAND_HELP = {
    "dialogue": "Run LangGraph user–agent dialogue(s); write results/exp_<model>_<ts>/ and log/ under it (or --artifact-dir).",
    "evaluate": "Run judge + verification + reward; optionally merge into task JSON.",
    "pass_hat_k": "Run Pass@k (k full pipeline repeats per task; optional Monte Carlo batches).",
    "verify": "Verify imports, config YAML, and optional secret resolution.",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _normalize_forwarded(forwarded: list[str]) -> list[str]:
    # Optional `--` after COMMAND separates wrapper argv from script argv (e.g. `AgenticPOIBench dialogue -- --help`).
    if forwarded and forwarded[0] == "--":
        return forwarded[1:]
    return forwarded


def _run_target(script: str, forwarded: list[str]) -> int:
    root = _repo_root()
    target = root / "scripts" / script
    if not target.is_file():
        print(f"Missing pipeline script: {target}", file=sys.stderr)
        return 2
    cmd = [sys.executable, str(target), *_normalize_forwarded(forwarded)]
    return subprocess.call(cmd, cwd=str(root))


def _build_parser() -> argparse.ArgumentParser:
    choices = tuple(sorted(_COMMAND_SCRIPTS.keys(), key=lambda c: (c.replace("_", "-"), c)))
    p = argparse.ArgumentParser(
        prog=_CLI_PROG,
        description=(
            "Primary entry for AgenticPOIBench pipelines. Forwards arguments to scripts under scripts/. "
            f"{_INDEX_HELP} Batch UI: --verbose, --quiet, --no-progress where supported."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            f"  ./{_CLI_PROG} dialogue --eval-index 0\n"
            f"  ./{_CLI_PROG} dialogue --start-index 1 --end-index 9\n"
            f"  ./{_CLI_PROG} evaluate --dry-run\n"
            f"  ./{_CLI_PROG} pass_hat_k --k 2 --eval-index 0\n"
            f"  ./{_CLI_PROG} verify --resolve-secrets\n"
            f"  ./{_CLI_PROG} dialogue -- --help   # optional `--` before script flags if needed\n"
            "\n"
            f"Direct `uv run python scripts/run_*.py` remains supported (legacy); prefer ./{_CLI_PROG}.\n"
            "\n"
            "Commands:\n"
            + "\n".join(
                f"  {name:12} {_COMMAND_HELP.get(name, '')}"
                for name in ("dialogue", "evaluate", "pass_hat_k", "verify")
            )
        ),
    )
    # One positional command plus REMAINDER so flags are forwarded (nested subparsers would eat them).
    p.add_argument(
        "command",
        choices=choices,
        metavar="COMMAND",
        help="Pipeline to run; all following tokens are passed to the underlying script.",
    )
    p.add_argument(
        "forwarded",
        nargs=argparse.REMAINDER,
        default=[],
        help="Arguments for the target script (see that script's --help).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = _build_parser()
    args = parser.parse_args(argv)
    script = _COMMAND_SCRIPTS[args.command]
    return _run_target(script, list(args.forwarded))


if __name__ == "__main__":
    raise SystemExit(main())
