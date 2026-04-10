# AgenticPOIBench: A Realistic Benchmark for Agentic Spatiotemporal-Constrained POI Search

**Modern POI search** demands have evolved beyond simple queries toward complex, long-tail tasks involving intricate spatiotemporal and semantic constraints. **LLM-based agents** offer a promising paradigm for tackling these challenges. **AgenticPOIBench** offers a challenging POI search benchmark by introducing four features that better capture real-world agent behavior:

- **Broad Coverage of Authentic Intents**: An LLM-aided pipeline generates a benchmark reflecting real-world user demands, comprising 199 samples and covering 25 semantic, spatial, and temporal constraints.

- **Multi-turn and Task Oriented User-Agent Interaction**: A dynamic framework assesses the agent's ability to track dialogue states, actively elicit missing constraints, and iteratively refine searches.

- **MCP Integration** — All tasks are executable through standard Model Context Protocol (MCP) interfaces connected to live map services from the Amap Platform, ensuring real-world evaluation.

- **Reproducible Verification** — Executable scripts are provided to ensure rigorous and reproducible performance assessments.


<p align="center">
  <img src="pics/figure3.png" alt="Figure 3" width="80%" />
</p>
<p align="center"><em>Benchmark advantage dimensions (to be paired with the summary table at the end of the document). A hyphen (--) denotes not applicable.</em></p>


## Overview

<p align="center">
  <img src="pics/figure2.png" alt="Figure 2" width="80%" />
</p>

<p align="center"><em></em></p>

**Agentic POI Bench** is a comprehensive benchmark for POI  search. Originating from **authentic user requirements**, it is built upon **real-world Model Context Protocol** rather than synthetic servers. It enables **objective and reproducible evaluations** through **task-oriented dialogues**.

## Quick Start

### 1. Install

```bash
git clone <YOUR_REPOSITORY_URL>
cd <repository-directory>
uv sync
```

This requires [uv](https://docs.astral.sh/uv/getting-started/installation/). If `./AgenticPOIBench` is not executable after clone, run `chmod +x AgenticPOIBench`.

Without `uv`, use a virtual environment and pinned dependencies:

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set up API keys

```bash
export AMAP_MCP_KEY=...      # Amap / Gaode key for live MCP map tools
export LITELLM_API_KEY=...   # LLM provider key (LiteLLM; any supported provider)
```

The environment variable names default to `AMAP_MCP_KEY` and `LITELLM_API_KEY`; you can rename them in `src/config/config.yaml` under the `env` section (`amap_key_env`, `llm_key_env`).

### 3. Run an evaluation

```bash
./AgenticPOIBench verify
./AgenticPOIBench verify --resolve-secrets   # optional: validate config + secret resolution when keys are set

./AgenticPOIBench dialogue --eval-index 0
# Or a small index range:
./AgenticPOIBench dialogue --start-index 0 --end-index 2
```

**Models:** The commands above do not pass model ids on the CLI. Defaults come from `src/config/config.yaml` under `llm.user_model`, `llm.agent_model`, and `llm.extract_model` (LiteLLM model ids). For `dialogue` and `pass_hat_k`, override per run with `--user-model` and `--agent-model`. For `evaluate`, use `--extract-model` only (re-runs the judge/extractor on existing task JSON). For example:

```bash
./AgenticPOIBench dialogue --eval-index 0 --agent-model openai/gpt-4o
```

This matches the usage described in `scripts/run_dialogue_once.py`. Set `LITELLM_API_KEY` to a key valid for the provider you select.

Artifacts are written under `results/exp_<agent_model>_<UTC_timestamp>/`; dialogue JSON logs live in that directory’s `log/` subfolder (unless you pass `--artifact-dir`).

**End-to-end vs. offline steps:** `dialogue` already runs the full benchmark loop for each sample: after the LangGraph dialogue finishes, the harness runs the POI judge, verification scripts, and reward, then writes task JSON (with an `evaluation` block) and `summary.json` when applicable. 

> **Tip:** Run `./AgenticPOIBench <COMMAND> --help` for full flags, or see [Available Commands](#available-commands) below. If the top-level parser interferes with script flags, use `./AgenticPOIBench dialogue -- --help`.

## Available Commands

| Command | Description |
|---------|-------------|
| `dialogue` | End-to-end: LangGraph user–agent dialogue(s), then judge, verify, and reward; writes `results/exp_<model>_<ts>/`, `log/`, and task JSON (or `--artifact-dir`). |
| `evaluate` | Re-run judge, verification, and reward on existing outputs; optionally merge into the task JSON. |
| `pass_hat_k` | `k` independent end-to-end runs per task (each is dialogue + evaluation); optional Monte Carlo batches. |
| `verify` | Check imports, config YAML, and optional secret resolution (e.g. `--resolve-secrets`). |

Use `./AgenticPOIBench <COMMAND> --help` for the target script’s full options. If parsing conflicts with top-level flags, insert `--` before script flags, e.g. `./AgenticPOIBench dialogue -- --help`.

---

## Project Structure

```
AgenticPOIBench/
├── AgenticPOIBench           # Repo-root CLI entry (bash → scripts/AgenticPOIBench.sh)
├── pyproject.toml            # Project metadata and dependencies (uv)
├── requirements.txt          # Pinned dependencies (pip / non-uv installs)
├── uv.lock                   # Lockfile for uv
├── README.md
├── data/
│   └── eval.json             # Benchmark eval tasks (default dataset; path configurable in config)
├── scripts/
│   ├── AgenticPOIBench.sh    # Invokes unified CLI with uv / venv / python3
│   ├── agentic_poi_bench_cli.py
│   ├── run_dialogue_once.py
│   ├── run_evaluate_once.py
│   ├── run_pass_at_k.py
│   ├── verify_env.py
│   └── setup_venv.sh
├── verify_scripts/           # Per-task verification scripts (automated checks)
├── pics/                     # Figures for the README
├── results/                  # Created at runtime (experiment outputs; typically gitignored)
└── src/
    ├── cli_batch.py          # Shared batch CLI flags and progress UI
    ├── concurrency.py        # MCP / LLM concurrency limits
    ├── experiment_paths.py   # Naming and layout under results/exp_*
    ├── config/               # config.yaml and settings loading
    ├── data/                 # Eval records and eval JSON ingestion
    ├── evaluation/           # validator, completed-run evaluation, Pass^k summaries
    ├── orchestration/        # LangGraph dialogue loop, Pass@k orchestration, run summaries
    ├── persistence/          # Dialogue and task JSON read/write
    ├── prompt/               # prompt.yaml 
    ├── simulation/           # User simulator and POI agent nodes
    └── tools/                # Amap MCP integration helpers
```

> **Note:** All benchmark task data for the default setup lives in `data/eval.json`; change `paths.eval_json` in `src/config/config.yaml` if you point to another file. 


## Documents

- [docs/](docs/) — supplementary documentation in the repository
- [Amap MCP key setup](docs/get_amap_mcp/get_amap_mcp.md) - How to get Amap MCP key
- [Seed constraints (中文)](docs/seed_constraints/seed_constraints_cn.md) - Seed constraints used in data synthesis(cn)
- [Seed constraints (English)](docs/seed_constraints/seed_constraints_en.md) - Seed constraints used in data synthesis(en)
