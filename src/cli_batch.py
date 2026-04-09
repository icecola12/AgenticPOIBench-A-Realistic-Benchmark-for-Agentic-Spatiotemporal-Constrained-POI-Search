"""
Shared helpers for batch-oriented scripts: log level tuning and optional task progress bars.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Iterable, Iterator, TypeVar

T = TypeVar("T")

def add_batch_ui_arguments(parser: argparse.ArgumentParser) -> None:
    """Register --verbose / --quiet / --no-progress on a script ArgumentParser."""
    g = parser.add_mutually_exclusive_group()
    g.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG logs from LiteLLM and HTTP client libraries.",
    )
    g.add_argument(
        "--quiet",
        action="store_true",
        help="Emit only ERROR-level logs from noisy libraries.",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable tqdm task progress bars (non-interactive stderr disables them automatically).",
    )


_NOISY_LOGGERS = (
    "litellm",
    "LiteLLM",
    "httpx",
    "httpcore",
    "openai",
    "urllib3",
    "mcp",
    "fastmcp",
)


def configure_run_logging(*, verbose: bool = False, quiet: bool = False) -> None:
    """
    Apply default / quiet / verbose log levels for library noise on stderr.

    LiteLLM also honors LITELLM_LOG; set it here so behavior matches stdlib loggers.
    """
    if verbose and quiet:
        raise ValueError("verbose and quiet are mutually exclusive")

    if verbose:
        root_level = logging.DEBUG
        os.environ["LITELLM_LOG"] = "DEBUG"
    elif quiet:
        root_level = logging.ERROR
        os.environ["LITELLM_LOG"] = "ERROR"
    else:
        root_level = logging.WARNING
        os.environ.setdefault("LITELLM_LOG", "WARNING")

    logging.basicConfig(
        level=root_level,
        format="%(levelname)s %(name)s: %(message)s",
        force=True,
    )
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(root_level)


def should_show_task_progress(
    *,
    no_progress: bool,
    num_tasks: int,
    batch_range: bool,
) -> bool:
    """Whether to show a tqdm bar: TTY, not opted out, and multi-task or explicit index range."""
    if no_progress or num_tasks == 0:
        return False
    if not sys.stderr.isatty():
        return False
    return num_tasks > 1 or batch_range


def iterate_tasks_with_progress(
    tasks: Iterable[T],
    *,
    show_progress: bool,
    desc: str,
) -> Iterator[T]:
    """Yield tasks, optionally wrapped in a tqdm progress bar (writes to stderr)."""
    if not show_progress:
        yield from tasks
        return

    from tqdm import tqdm

    # Materialize once so tqdm knows total without consuming a generator twice.
    seq = list(tasks)
    yield from tqdm(
        seq,
        desc=desc,
        unit="task",
        dynamic_ncols=True,
        file=sys.stderr,
    )
