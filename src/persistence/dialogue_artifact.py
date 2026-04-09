"""
Build and write dialogue exports aligned with benchmark bundles: task, trajectory.steps,
user_visible_history (public transcript + synthetic opening line), and full_history
(compact messages, same step metadata as trajectory).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from data.ingestion import EvalRecord

from experiment_paths import make_experiment_run_dir

# Opening line shown to the user in exported visible history (turn_idx 0), matching benchmark bundles.
_VISIBLE_OPENING_ASSISTANT = (
    "您好！我是智能地点筛选助手，专门帮您查找符合条件的地点。"
    "请告诉我您想找什么样的地方，我会为您提供准确的信息。"
)


def default_artifact_dir(project_root: Path) -> Path:
    """Default directory when callers omit artifact_dir: new results/exp_default_<timestamp>/ folder."""
    return make_experiment_run_dir(project_root, "default")


def find_task_artifact_json(
    artifact_dir: Path,
    task_id: int,
    *,
    preferred_label: str | None = "manual",
) -> Path:
    """
    Locate task_<id>_<label>.json under artifact_dir.

    Tries preferred_label first (after safe filename normalization); if missing, uses any
    task_<id>_*.json, preferring the newest file by mtime when several exist.
    """
    if not artifact_dir.is_dir():
        raise FileNotFoundError(f"Artifact directory not found: {artifact_dir}")
    tid = int(task_id)
    if preferred_label is not None and str(preferred_label).strip():
        label = _safe_filename_label(preferred_label)
        candidate = artifact_dir / f"task_{tid}_{label}.json"
        if candidate.is_file():
            return candidate
    matches = sorted(artifact_dir.glob(f"task_{tid}_*.json"))
    if not matches:
        raise FileNotFoundError(f"No task JSON for task_id={tid} under {artifact_dir}")
    if len(matches) == 1:
        return matches[0]
    return max(matches, key=lambda p: p.stat().st_mtime)


def _safe_filename_label(label: str | None) -> str:
    if not label or not str(label).strip():
        return uuid4().hex[:8]
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", str(label).strip())
    return cleaned[:64] if cleaned else uuid4().hex[:8]


def _stringify_content(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    try:
        return json.dumps(content, ensure_ascii=False)
    except TypeError:
        return str(content)


def _parse_tool_arguments_json(arguments: str) -> tuple[Any, bool]:
    """Return (parsed dict/list/primitive, parse_error)."""
    raw = (arguments or "").strip()
    if not raw:
        return {}, False
    try:
        parsed: Any = json.loads(raw)
        return parsed, False
    except json.JSONDecodeError:
        return raw, True


def _openai_tool_calls_to_trajectory_format(
    tool_calls: list[dict[str, Any]] | None,
) -> list[dict[str, Any]] | None:
    if not tool_calls:
        return None
    out: list[dict[str, Any]] = []
    for tc in tool_calls:
        fn = tc.get("function") if isinstance(tc, dict) else None
        if not isinstance(fn, dict):
            fn = {}
        name = fn.get("name") or ""
        args_str = fn.get("arguments")
        if not isinstance(args_str, str):
            args_str = json.dumps(args_str) if args_str is not None else "{}"
        parsed, parse_err = _parse_tool_arguments_json(args_str)
        arguments_raw: Any = parsed if not parse_err else args_str
        out.append(
            {
                "id": tc.get("id") or "",
                "name": name,
                "arguments_raw": arguments_raw,
                "arguments": None,
                "parse_error": parse_err,
            }
        )
    return out or None


def _normalize_graph_message_for_trajectory(msg: dict[str, Any]) -> dict[str, Any]:
    """Map one LangGraph / LiteLLM message dict to the trajectory message object shape."""
    role = msg.get("role") or "assistant"
    content = _stringify_content(msg.get("content"))
    tool_call_id = msg.get("tool_call_id")
    tool_call_id_out = tool_call_id if isinstance(tool_call_id, str) and tool_call_id else None

    tool_calls_out: list[dict[str, Any]] | None = None
    if role == "assistant" and msg.get("tool_calls"):
        raw_tcs = msg.get("tool_calls")
        if isinstance(raw_tcs, list):
            tool_calls_out = _openai_tool_calls_to_trajectory_format(raw_tcs)

    return {
        "role": role,
        "content": content,
        "tool_calls": tool_calls_out,
        "tool_call_id": tool_call_id_out,
        "reasoning_content": None,
    }


def _turn_idx_for_message_sequence(messages: list[dict[str, Any]]) -> list[int]:
    """Increment turn index on each user message; assistant/tool keep current index."""
    turn = 0
    indices: list[int] = []
    for m in messages:
        if m.get("role") == "user":
            turn += 1
        indices.append(turn)
    return indices


def _transcript_messages(agent_messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop system prompts; keep user/assistant/tool rows in order."""
    return [m for m in agent_messages if m.get("role") != "system"]


def build_task_section(record: EvalRecord) -> dict[str, Any]:
    """Static task fields from the eval record."""
    task: dict[str, Any] = {
        "id": str(record.id),
        "user_instructions": record.user_instruction.strip(),
        "location": record.user_address.strip(),
        "location_coordinate": record.user_location.strip(),
        "time": record.time.strip(),
        "background_information": (record.background_information or "").strip(),
        "all_poi": list(record.all_poi),
    }
    if (record.candidate_list or "").strip():
        task["candidate_list"] = record.candidate_list.strip()
    return task


def _transcript_step_rows(
    transcript: list[dict[str, Any]],
    start_time: datetime,
    end_time: datetime,
) -> list[tuple[int, int, datetime, dict[str, Any]]]:
    """Per-message step index, turn_idx, timestamp, and raw message dict."""
    turn_indices = _turn_idx_for_message_sequence(transcript)
    duration = end_time - start_time
    total_sec = duration.total_seconds()
    n = len(transcript)
    rows: list[tuple[int, int, datetime, dict[str, Any]]] = []
    for i, msg in enumerate(transcript):
        if n <= 1:
            ts = start_time
        else:
            ts = start_time + timedelta(seconds=total_sec * i / (n - 1))
        rows.append((i, turn_indices[i], ts, msg))
    return rows


def _termination_reason(
    termination_flag: bool,
    current_turn: int,
    max_turns: int,
) -> str:
    if termination_flag:
        return "user_stop"
    if current_turn >= max_turns:
        return "max_turns"
    return "graph_end"


def _trajectory_step_tool_calls_to_openai(tcs: list[Any]) -> list[dict[str, Any]]:
    """Map trajectory-style tool_calls back to OpenAI-like chunks for metric helpers."""
    out: list[dict[str, Any]] = []
    for tc in tcs:
        if not isinstance(tc, dict):
            continue
        raw = tc.get("arguments_raw")
        if isinstance(raw, str):
            args_str = raw
        else:
            args_str = json.dumps(raw, ensure_ascii=False) if raw is not None else "{}"
        out.append(
            {
                "id": tc.get("id") or "",
                "type": "function",
                "function": {"name": tc.get("name") or "", "arguments": args_str},
            }
        )
    return out


def agent_messages_from_trajectory_doc(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Rebuild agent-side transcript from a saved task JSON trajectory.steps (for offline evaluation)."""
    traj = doc.get("trajectory")
    if not isinstance(traj, dict):
        return []
    steps = traj.get("steps")
    if not isinstance(steps, list):
        return []
    out: list[dict[str, Any]] = []
    for step in steps:
        if not isinstance(step, dict):
            continue
        msg = step.get("message")
        if not isinstance(msg, dict):
            continue
        role = msg.get("role") or "assistant"
        row: dict[str, Any] = {"role": role, "content": _stringify_content(msg.get("content"))}
        raw_tcs = msg.get("tool_calls")
        if isinstance(raw_tcs, list) and raw_tcs:
            row["tool_calls"] = _trajectory_step_tool_calls_to_openai(raw_tcs)
        tid = msg.get("tool_call_id")
        if isinstance(tid, str) and tid.strip():
            row["tool_call_id"] = tid
        out.append(row)
    return out


def infer_dialogue_flags_from_artifact(
    doc: dict[str, Any],
    *,
    default_max_turns: int,
) -> tuple[bool, int, int]:
    """
    Best-effort termination_flag, current_turn, max_turns from a saved artifact
    when agent state is not available.
    """
    traj = doc.get("trajectory")
    term = "graph_end"
    if isinstance(traj, dict):
        tr = traj.get("termination_reason")
        if isinstance(tr, str):
            term = tr
    termination_flag = term == "user_stop"
    turns: list[int] = []
    uvh = doc.get("user_visible_history")
    if isinstance(uvh, list):
        for row in uvh:
            if isinstance(row, dict) and "turn_idx" in row:
                try:
                    turns.append(int(row["turn_idx"]))
                except (TypeError, ValueError):
                    pass
    current_turn = max(turns) if turns else 0
    return termination_flag, current_turn, int(default_max_turns)


def compute_evaluation_tool_and_step_metrics(
    agent_messages: list[dict[str, Any]],
    *,
    termination_flag: bool,
    current_turn: int,
    max_turns: int,
) -> dict[str, Any]:
    """
    Fields aligned with benchmark evaluation JSON: step count, termination_reason, tool call tallies.
    """
    transcript = _transcript_messages(agent_messages)
    step_count = len(transcript)
    total = 0
    invalid_json = 0
    for msg in transcript:
        if msg.get("role") != "assistant":
            continue
        norm = _normalize_graph_message_for_trajectory(msg)
        tcs = norm.get("tool_calls")
        if not isinstance(tcs, list):
            continue
        for tc in tcs:
            total += 1
            if tc.get("parse_error"):
                invalid_json += 1
    return {
        "termination_reason": _termination_reason(termination_flag, current_turn, max_turns),
        "step": step_count,
        "tool_calls_total": total,
        "tool_calls_invalid_json": invalid_json,
    }


def _arguments_to_json_string(arguments: Any) -> str:
    if isinstance(arguments, str):
        return arguments
    try:
        return json.dumps(arguments, ensure_ascii=False)
    except TypeError:
        return str(arguments)


def _compact_message_for_full_history(msg: dict[str, Any]) -> dict[str, Any]:
    """Minimal OpenAI-like message shape for full_history (not trajectory.steps)."""
    role = msg.get("role") or "assistant"
    content = _stringify_content(msg.get("content"))

    if role == "user":
        return {"role": "user", "content": content}

    if role == "tool":
        tid = msg.get("tool_call_id")
        tid_out = tid if isinstance(tid, str) else str(tid or "")
        return {"role": "tool", "tool_call_id": tid_out, "content": content}

    # assistant
    raw_tcs = msg.get("tool_calls")
    if not raw_tcs or not isinstance(raw_tcs, list):
        return {"role": "assistant", "content": content}

    openai_calls: list[dict[str, Any]] = []
    for tc in raw_tcs:
        if not isinstance(tc, dict):
            continue
        fn = tc.get("function")
        if isinstance(fn, dict) and fn.get("name") is not None:
            args = fn.get("arguments", "{}")
            args_str = args if isinstance(args, str) else _arguments_to_json_string(args)
            openai_calls.append(
                {
                    "id": tc.get("id") or "",
                    "type": "function",
                    "function": {
                        "name": fn.get("name") or "",
                        "arguments": args_str,
                    },
                }
            )
            continue
        # Normalized trajectory-style tool call on the wire
        name = tc.get("name") or ""
        raw_args = tc.get("arguments_raw")
        if raw_args is not None and not isinstance(raw_args, str):
            args_str = _arguments_to_json_string(raw_args)
        else:
            args_str = str(raw_args) if raw_args is not None else "{}"
        openai_calls.append(
            {
                "id": tc.get("id") or "",
                "type": "function",
                "function": {"name": name, "arguments": args_str},
            }
        )

    if not openai_calls:
        return {"role": "assistant", "content": content}
    return {"role": "assistant", "content": content, "tool_calls": openai_calls}


def build_user_visible_history(
    public_messages: list[dict[str, Any]],
    *,
    start_time: datetime,
    end_time: datetime,
) -> list[dict[str, Any]]:
    """
    User-facing transcript only: synthetic opening assistant (turn 0) plus public_messages.
    turn_idx increments on each user message; assistant lines reuse the current index.
    """
    rows: list[dict[str, Any]] = []
    turn = 0
    opener = {
        "turn_idx": 0,
        "role": "assistant",
        "content": _VISIBLE_OPENING_ASSISTANT.strip(),
    }
    pending: list[dict[str, Any]] = [opener]
    for msg in public_messages:
        role = msg.get("role") or "user"
        if role == "user":
            turn += 1
        pending.append(
            {
                "turn_idx": turn,
                "role": role,
                "content": _stringify_content(msg.get("content")),
            }
        )

    duration = end_time - start_time
    total_sec = duration.total_seconds()
    n = len(pending)
    for i, item in enumerate(pending):
        if n <= 1:
            ts = start_time
        else:
            ts = start_time + timedelta(seconds=total_sec * i / (n - 1))
        rows.append({**item, "timestamp": ts.isoformat()})
    return rows


def build_full_history(
    agent_messages: list[dict[str, Any]],
    *,
    start_time: datetime,
    end_time: datetime,
) -> list[dict[str, Any]]:
    """Same step/turn/timestamp as trajectory.steps; compact message payloads."""
    transcript = _transcript_messages(agent_messages)
    meta = _transcript_step_rows(transcript, start_time, end_time)
    out: list[dict[str, Any]] = []
    for step_i, turn_i, ts, msg in meta:
        out.append(
            {
                "step": step_i,
                "turn_idx": turn_i,
                "from_role": msg.get("role") or "assistant",
                "timestamp": ts.isoformat(),
                "message": _compact_message_for_full_history(msg),
            }
        )
    return out


def build_trajectory_section(
    record: EvalRecord,
    agent_messages: list[dict[str, Any]],
    *,
    start_time: datetime,
    end_time: datetime,
    termination_flag: bool,
    current_turn: int,
    max_turns: int,
) -> dict[str, Any]:
    """Ordered steps from the agent-side transcript (includes tool calls and results)."""
    transcript = _transcript_messages(agent_messages)
    meta = _transcript_step_rows(transcript, start_time, end_time)
    steps_out: list[dict[str, Any]] = []
    for step_i, turn_i, ts, msg in meta:
        steps_out.append(
            {
                "step": step_i,
                "turn_idx": turn_i,
                "from_role": msg.get("role") or "assistant",
                "message": _normalize_graph_message_for_trajectory(msg),
                "timestamp": ts.isoformat(),
            }
        )

    return {
        "task_id": str(record.id),
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "termination_reason": _termination_reason(termination_flag, current_turn, max_turns),
        "steps": steps_out,
    }


def build_final_data_payload(
    record: EvalRecord,
    *,
    agent_messages: list[dict[str, Any]],
    public_messages: list[dict[str, Any]],
    start_time: datetime,
    end_time: datetime,
    termination_flag: bool,
    current_turn: int,
    max_turns: int,
    evaluation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Full document: task, trajectory, user-visible history, full_history, and optional evaluation."""
    payload: dict[str, Any] = {
        "task": build_task_section(record),
        "trajectory": build_trajectory_section(
            record,
            agent_messages,
            start_time=start_time,
            end_time=end_time,
            termination_flag=termination_flag,
            current_turn=current_turn,
            max_turns=max_turns,
        ),
        "user_visible_history": build_user_visible_history(
            public_messages,
            start_time=start_time,
            end_time=end_time,
        ),
        "full_history": build_full_history(
            agent_messages,
            start_time=start_time,
            end_time=end_time,
        ),
    }
    if evaluation is not None:
        payload["evaluation"] = evaluation
    return payload


def write_final_data_dialogue(
    artifact_dir: Path,
    record: EvalRecord,
    *,
    agent_messages: list[dict[str, Any]],
    public_messages: list[dict[str, Any]],
    start_time: datetime,
    end_time: datetime,
    termination_flag: bool,
    current_turn: int,
    max_turns: int,
    run_label: str | None = None,
    evaluation: dict[str, Any] | None = None,
) -> Path:
    """
    Write one JSON file: task, trajectory, user_visible_history, full_history, evaluation (if provided).
    Filename: task_<id>_<label>.json
    """
    artifact_dir.mkdir(parents=True, exist_ok=True)
    label = _safe_filename_label(run_label)
    path = artifact_dir / f"task_{record.id}_{label}.json"
    payload = build_final_data_payload(
        record,
        agent_messages=agent_messages,
        public_messages=public_messages,
        start_time=start_time,
        end_time=end_time,
        termination_flag=termination_flag,
        current_turn=current_turn,
        max_turns=max_turns,
        evaluation=evaluation,
    )
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
