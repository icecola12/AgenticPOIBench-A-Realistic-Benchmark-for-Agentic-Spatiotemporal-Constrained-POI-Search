"""
Verify that the Python environment can import Harness dependencies and that config.yaml parses
(infrastructure / configuration checks).

Usage (from repo root)::

    # With uv:
    uv run python scripts/verify_env.py

    # Without uv, venv + pip (install deps first):
    python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
    pip install -r requirements.txt
    PYTHONPATH=src python scripts/verify_env.py

If AMAP_MCP_KEY and LITELLM_API_KEY are set (names follow config.yaml), add --resolve-secrets
to also validate resolve_secrets / load_resolved_config.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path


def _try_import(name: str) -> None:
    importlib.import_module(name)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify dependencies and config loading")
    parser.add_argument(
        "--resolve-secrets",
        action="store_true",
        help="If env vars are set, also verify resolve_secrets / load_resolved_config",
    )
    args = parser.parse_args()

    modules = (
        "yaml",
        "pydantic",
        "litellm",
        "langgraph",
        "requests",
    )
    failed: list[str] = []
    for m in modules:
        try:
            _try_import(m)
        except Exception as e:  # noqa: BLE001 — aggregate report
            failed.append(f"{m}: {e!r}")
    if failed:
        print("Environment check failed (missing or failed import):", file=sys.stderr)
        for line in failed:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print("Environment OK, imports verified:")
    for m in modules:
        print(f"  - {m}")

    root = _repo_root()
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    try:
        from config import load_app_settings, load_resolved_config  # noqa: E402  # pyright: ignore[reportMissingImports]
    except Exception as e:  # noqa: BLE001
        print(f"Cannot import src.config: {e!r}", file=sys.stderr)
        return 1

    try:
        settings, _ = load_app_settings(project_root=root)
    except Exception as e:  # noqa: BLE001
        print(f"config.yaml parse failed: {e!r}", file=sys.stderr)
        return 1

    e = settings.env
    print("Config loaded (YAML):")
    print(f"  - Amap key env var: {e.amap_key_env}")
    print(f"  - LLM key env var: {e.llm_key_env}")
    print(f"  - LLM API base override (optional): {e.llm_api_base_env}")

    try:
        from concurrency import concurrency_limits, init_concurrency  # noqa: E402
    except Exception as err:  # noqa: BLE001
        print(f"Failed to import concurrency module: {err!r}", file=sys.stderr)
        return 1

    init_concurrency(settings)
    mcp_n, llm_n = concurrency_limits()
    if mcp_n != settings.mcp.max_concurrent_mcp or llm_n != settings.llm.max_concurrent_llm:
        print(
            "Concurrency caps do not match config.yaml: "
            f"mcp expected {settings.mcp.max_concurrent_mcp} got {mcp_n}; "
            f"llm expected {settings.llm.max_concurrent_llm} got {llm_n}",
            file=sys.stderr,
        )
        return 1
    print("Concurrency module OK:")
    print(f"  - MCP cap (mcp.max_concurrent_mcp): {mcp_n}")
    print(f"  - LLM cap (llm.max_concurrent_llm): {llm_n}")

    if args.resolve_secrets:
        try:
            load_resolved_config(project_root=root)
        except Exception as err:  # noqa: BLE001
            print(
                f"--resolve-secrets failed (check env vars above are exported): {err!r}",
                file=sys.stderr,
            )
            return 1
        print("Secrets OK: load_resolved_config passed.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
