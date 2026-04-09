#!/usr/bin/env bash
# Run unified AgenticPOIBench CLI from repo root (uv preferred, else .venv or python3).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
CLI_PY="$ROOT/scripts/agentic_poi_bench_cli.py"
if command -v uv >/dev/null 2>&1; then
  exec uv run python "$CLI_PY" "$@"
fi
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  exec "$ROOT/.venv/bin/python" "$CLI_PY" "$@"
fi
exec python3 "$CLI_PY" "$@"
