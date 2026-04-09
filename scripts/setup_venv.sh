#!/usr/bin/env bash
# 在仓库根目录创建/更新 .venv 并安装依赖（不依赖 uv）。可从任意目录调用：
#   bash /path/to/repo/scripts/setup_venv.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if ! command -v python3 >/dev/null 2>&1; then
  echo "please install python3" >&2
  exit 1
fi
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/verify_env.py
