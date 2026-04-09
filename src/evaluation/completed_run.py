"""
Assemble the evaluation section after a dialogue: LLM judge, tool metrics, verify scripts, reward.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from config import ResolvedConfig
from data import EvalRecord, ExtractorInit
from data.ingestion import parse_user_visible_history_from_artifact
from evaluation.extractor import evaluation_fields_from_judge, run_extractor
from evaluation.validator import merge_validation_into_evaluation, run_validation_and_reward_safe
from persistence.dialogue_artifact import (
    agent_messages_from_trajectory_doc,
    build_user_visible_history,
    compute_evaluation_tool_and_step_metrics,
    infer_dialogue_flags_from_artifact,
)


async def build_evaluation_for_completed_run(
    resolved: ResolvedConfig,
    record: EvalRecord,
    *,
    agent_messages: list[dict[str, Any]],
    public_messages: list[dict[str, Any]],
    start_time: datetime,
    end_time: datetime,
    termination_flag: bool,
    current_turn: int,
    max_turns: int,
) -> dict[str, Any]:
    """
    Full evaluation block: metrics, extractor judge output, verify_scripts, binary reward.
    """
    visible_rows = build_user_visible_history(
        public_messages,
        start_time=start_time,
        end_time=end_time,
    )
    init = ExtractorInit.from_record_and_visible_rows(record, visible_rows)
    judge = await run_extractor(resolved, init)
    judge_fields = evaluation_fields_from_judge(judge)
    metrics = compute_evaluation_tool_and_step_metrics(
        agent_messages,
        termination_flag=termination_flag,
        current_turn=current_turn,
        max_turns=max_turns,
    )
    base_eval: dict[str, Any] = {**metrics, **judge_fields}
    report = run_validation_and_reward_safe(
        recommended_poi_ids=judge_fields["recommended_poi_ids"],
        ground_truth_all_poi=record.all_poi,
        task_id=int(record.id),
        verify_scripts_dir=resolved.verify_scripts_dir,
        user_location=record.user_location.strip(),
    )
    return merge_validation_into_evaluation(
        base_eval,
        report,
        ground_truth_all_poi=list(record.all_poi),
        recommended_order=list(judge_fields["recommended_poi_ids"]),
    )


def _parse_trajectory_times(traj: dict[str, Any]) -> tuple[datetime, datetime]:
    start_raw = traj.get("start_time")
    end_raw = traj.get("end_time")
    if not isinstance(start_raw, str) or not isinstance(end_raw, str):
        raise ValueError("trajectory start_time/end_time must be ISO strings")
    start_s = start_raw.replace("Z", "+00:00")
    end_s = end_raw.replace("Z", "+00:00")
    return datetime.fromisoformat(start_s), datetime.fromisoformat(end_s)


async def build_evaluation_for_saved_artifact(
    resolved: ResolvedConfig,
    record: EvalRecord,
    doc: dict[str, Any],
) -> dict[str, Any]:
    """
    Build evaluation from an on-disk task JSON (trajectory + user_visible_history), no live agent state.
    """
    traj = doc.get("trajectory")
    if not isinstance(traj, dict):
        raise ValueError("artifact missing trajectory section")
    start_time, end_time = _parse_trajectory_times(traj)
    entries = parse_user_visible_history_from_artifact(doc)
    init = ExtractorInit.from_record_and_visible_rows(record, entries)
    agent_messages = agent_messages_from_trajectory_doc(doc)
    term, cur, mx = infer_dialogue_flags_from_artifact(
        doc,
        default_max_turns=resolved.settings.dialog.max_turns,
    )
    judge = await run_extractor(resolved, init)
    judge_fields = evaluation_fields_from_judge(judge)
    metrics = compute_evaluation_tool_and_step_metrics(
        agent_messages,
        termination_flag=term,
        current_turn=cur,
        max_turns=mx,
    )
    base_eval: dict[str, Any] = {**metrics, **judge_fields}
    report = run_validation_and_reward_safe(
        recommended_poi_ids=judge_fields["recommended_poi_ids"],
        ground_truth_all_poi=record.all_poi,
        task_id=int(record.id),
        verify_scripts_dir=resolved.verify_scripts_dir,
        user_location=record.user_location.strip(),
    )
    return merge_validation_into_evaluation(
        base_eval,
        report,
        ground_truth_all_poi=list(record.all_poi),
        recommended_order=list(judge_fields["recommended_poi_ids"]),
    )
