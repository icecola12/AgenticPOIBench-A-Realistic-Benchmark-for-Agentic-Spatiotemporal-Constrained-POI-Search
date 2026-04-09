"""
LangGraph loop: User Simulator and Agent alternate until stop token or max turns.
Writes dialogue JSON logs under log_dir (default <artifact_dir>/log) and task+trajectory JSON
under artifact_dir (default a new <project_root>/results/exp_default_<timestamp>/ folder).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from config import ResolvedConfig, load_resolved_config
from concurrency import init_concurrency
from data import AgentInit, EvalRecord, UserSimulatorInit
from evaluation import build_evaluation_for_completed_run
from persistence import default_artifact_dir, write_final_data_dialogue
from simulation import POIAgent, UserSimulator


class AgentState(TypedDict):
    """
    Graph state: two transcripts — user-facing vs agent-internal.

    public_messages: alternating user/assistant plain text for the User Simulator and readable logs.
    agent_messages: same user lines plus full assistant/tool/tool_result chain for POIAgent context.
    """

    public_messages: list[dict[str, Any]]
    agent_messages: list[dict[str, Any]]
    current_turn: int
    max_turns: int
    user_instruction: str
    termination_flag: bool


@dataclass(frozen=True)
class DialogueRunResult:
    """Outcome of one dialogue + evaluation write (for Pass@k and callers that need reward)."""

    final_state: AgentState
    evaluation: dict[str, Any]
    artifact_path: Path


def default_log_dir(project_root: Path) -> Path:
    """Optional explicit log root (e.g. project_root/test/log) when callers set log_dir manually."""
    return (project_root / "test" / "log").resolve()


def _public_assistant_text(agent_new_messages: list[dict[str, Any]]) -> str:
    """Take the last assistant message in one agent turn (after any tool sub-rounds)."""
    for msg in reversed(agent_new_messages):
        if msg.get("role") != "assistant":
            continue
        raw = msg.get("content")
        return "" if raw is None else str(raw)
    return ""


def write_dialogue_log(
    log_dir: Path,
    final_state: AgentState,
    *,
    eval_sample_id: int | None = None,
    run_label: str | None = None,
) -> Path:
    """Serialize final_state and metadata to a new JSON file under log_dir."""
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    suffix = uuid4().hex[:8]
    name = f"dialogue_{stamp}_{suffix}.json"
    path = log_dir / name
    payload: dict[str, Any] = {
        "written_at_utc": datetime.now(timezone.utc).isoformat(),
        "eval_sample_id": eval_sample_id,
        "run_label": run_label,
        "state": dict(final_state),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def build_compiled_interaction_graph(
    user_sim: UserSimulator,
    poi_agent: POIAgent,
) -> CompiledStateGraph:
    """
    Build and compile a graph: START -> user_sim -> (agent | END) -> (user_sim | END).
    Routing uses stop token (stored in termination_flag) and current_turn >= max_turns.
    """

    async def user_sim_node(state: AgentState) -> dict[str, Any]:
        public = state["public_messages"]
        agent_ctx = state["agent_messages"]
        user_msg, hit_stop = await user_sim.generate_user_message(public)
        return {
            "public_messages": [*public, user_msg],
            "agent_messages": [*agent_ctx, user_msg],
            "termination_flag": bool(hit_stop),
        }

    async def agent_node(state: AgentState) -> dict[str, Any]:
        dialogue = state["agent_messages"]
        agent_chunks = await poi_agent.generate_reply(dialogue)
        text = _public_assistant_text(agent_chunks)
        assistant_msg: dict[str, Any] = {"role": "assistant", "content": text}
        return {
            "agent_messages": [*dialogue, *agent_chunks],
            "public_messages": [*state["public_messages"], assistant_msg],
            "current_turn": state["current_turn"] + 1,
        }

    def route_after_user(state: AgentState) -> Literal["agent", "end"]:
        if state["termination_flag"]:
            return "end"
        return "agent"

    def route_after_agent(state: AgentState) -> Literal["user_sim", "end"]:
        if state["current_turn"] >= state["max_turns"]:
            return "end"
        return "user_sim"

    graph = StateGraph(AgentState)
    graph.add_node("user_sim", user_sim_node)
    graph.add_node("agent", agent_node)
    graph.add_edge(START, "user_sim")
    graph.add_conditional_edges(
        "user_sim",
        route_after_user,
        {"agent": "agent", "end": END},
    )
    graph.add_conditional_edges(
        "agent",
        route_after_agent,
        {"user_sim": "user_sim", "end": END},
    )
    return graph.compile()


async def run_dialogue_loop(
    resolved: ResolvedConfig,
    record: EvalRecord,
    *,
    log_dir: Path | None = None,
    artifact_dir: Path | None = None,
    run_label: str | None = None,
) -> DialogueRunResult:
    """
    Initialize concurrency, simulators, run the compiled graph, then write a log file.
    Also writes a task+trajectory JSON under artifact_dir (final_data-style layout).
    Returns final graph state, the evaluation dict, and the written artifact path.
    """
    init_concurrency(resolved.settings)
    user_sim = UserSimulator.from_init(resolved, UserSimulatorInit.from_record(record))
    poi_agent = POIAgent.from_init(resolved, AgentInit.from_record(record))
    app = build_compiled_interaction_graph(user_sim, poi_agent)
    initial: AgentState = {
        "public_messages": [],
        "agent_messages": [],
        "current_turn": 0,
        "max_turns": resolved.settings.dialog.max_turns,
        "user_instruction": record.user_instruction.strip(),
        "termination_flag": False,
    }
    start_ts = datetime.now(timezone.utc)
    final: AgentState = await app.ainvoke(initial)
    end_ts = datetime.now(timezone.utc)
    final_data_dir = artifact_dir if artifact_dir is not None else default_artifact_dir(resolved.project_root)
    out_dir = log_dir if log_dir is not None else (final_data_dir / "log")
    write_dialogue_log(
        out_dir,
        final,
        eval_sample_id=record.id,
        run_label=run_label,
    )
    evaluation = await build_evaluation_for_completed_run(
        resolved,
        record,
        agent_messages=final["agent_messages"],
        public_messages=final["public_messages"],
        start_time=start_ts,
        end_time=end_ts,
        termination_flag=bool(final["termination_flag"]),
        current_turn=int(final["current_turn"]),
        max_turns=int(final["max_turns"]),
    )
    artifact_path = write_final_data_dialogue(
        final_data_dir,
        record,
        agent_messages=final["agent_messages"],
        public_messages=final["public_messages"],
        start_time=start_ts,
        end_time=end_ts,
        termination_flag=bool(final["termination_flag"]),
        current_turn=int(final["current_turn"]),
        max_turns=int(final["max_turns"]),
        run_label=run_label,
        evaluation=evaluation,
    )
    return DialogueRunResult(final_state=final, evaluation=evaluation, artifact_path=artifact_path)


async def run_dialogue_loop_from_env(
    record: EvalRecord,
    *,
    log_dir: Path | None = None,
    run_label: str | None = None,
) -> DialogueRunResult:
    """load_resolved_config() from default paths, then run_dialogue_loop."""
    resolved = load_resolved_config()
    return await run_dialogue_loop(
        resolved,
        record,
        log_dir=log_dir,
        run_label=run_label,
    )
