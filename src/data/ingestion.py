"""
Eval data ingestion: load eval JSON, validate records, and build init payloads for prompts.

Maps dataset fields to template placeholders: address text vs. coordinate string vs. time string.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class EvalRecord(BaseModel):
    """One benchmark sample; matches entries in data/eval.json."""

    id: int
    time: str
    user_location: str
    user_address: str
    background_information: str = ""
    user_instruction: str
    all_poi: list[str] = Field(default_factory=list)
    candidate_list: str = ""

    @field_validator("user_instruction", "user_address", "user_location", "time")
    @classmethod
    def _non_empty_str(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("user_instruction, user_address, user_location, and time must be non-empty strings")
        return v


@dataclass(frozen=True)
class UserSimulatorInit:
    """Context for formatting the User Simulator system prompt on turn 1 (prompt.yaml placeholders)."""

    user_instruction: str
    location: str

    @classmethod
    def from_record(cls, record: EvalRecord) -> UserSimulatorInit:
        return cls(
            user_instruction=record.user_instruction.strip(),
            location=record.user_address.strip(),
        )

    def prompt_format_kwargs(self) -> dict[str, str]:
        """Kwargs for str.format(**kwargs) or template.format_map(...)."""
        return {
            "user_instruction": self.user_instruction,
            "location": self.location,
        }


@dataclass(frozen=True)
class AgentInit:
    """Spatiotemporal context for the Agent system prompt (address, lng/lat pair, scenario time)."""

    location: str
    coordinate: str
    time: str

    @classmethod
    def from_record(cls, record: EvalRecord) -> AgentInit:
        return cls(
            location=record.user_address.strip(),
            coordinate=record.user_location.strip(),
            time=record.time.strip(),
        )

    def prompt_format_kwargs(self) -> dict[str, str]:
        """Keys match Agent template placeholders (coordinate aliases for YAML naming)."""
        return {
            "location": self.location,
            "coordinate": self.coordinate,
            "location_coordinate": self.coordinate,
            "time": self.time,
        }


def load_eval_json(path: Path | str) -> list[EvalRecord]:
    """
    Load eval JSON (top-level array of objects), validate, return list of EvalRecord.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Eval data file not found: {p}")
    raw_text = p.read_text(encoding="utf-8")
    raw: Any = json.loads(raw_text)
    if not isinstance(raw, list):
        raise ValueError(f"Eval JSON top level must be an array: {p}")
    return [EvalRecord.model_validate(item) for item in raw]


def load_eval_json_from_config_eval_path(project_root: Path, eval_json_relative: str) -> list[EvalRecord]:
    """Resolve paths.eval_json relative to repo root (per config.yaml), then load."""
    rel = Path(eval_json_relative)
    path = rel if rel.is_absolute() else (project_root / rel).resolve()
    return load_eval_json(path)


def select_eval_records_for_cli_indices(
    records: list[EvalRecord],
    *,
    eval_index: int,
    start_index: int | None,
    end_index_inclusive: int | None,
) -> list[EvalRecord]:
    """
    Return eval records for a single index or for an inclusive [start, end] slice (0-based).

    Range mode is used when either start or end is set; then both must be set.
    Single-index mode uses eval_index when no range is requested.
    """
    n = len(records)
    if n == 0:
        raise ValueError("eval record list is empty")
    range_requested = start_index is not None or end_index_inclusive is not None
    if range_requested:
        if start_index is None or end_index_inclusive is None:
            raise ValueError("Both start_index and end_index_inclusive are required for a range")
        start = start_index
        end = end_index_inclusive
        if start < 0 or end < 0:
            raise ValueError("eval indices must be non-negative")
        if start > end:
            raise ValueError("start_index must be <= end_index (inclusive)")
        if end >= n:
            raise ValueError(
                f"end_index {end} out of range for {n} eval record(s); valid inclusive end is 0..{n - 1}"
            )
        if start >= n:
            raise ValueError(
                f"start_index {start} out of range for {n} eval record(s); valid start is 0..{n - 1}"
            )
        return records[start : end + 1]
    if eval_index < 0 or eval_index >= n:
        raise ValueError(f"eval_index {eval_index} out of range for {n} eval record(s)")
    return [records[eval_index]]


def load_dialogue_artifact_json(path: Path | str) -> dict[str, Any]:
    """Load a dialogue export object (task, trajectory, user_visible_history, ...)."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Dialogue artifact file not found: {p}")
    raw: Any = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Dialogue JSON top level must be an object: {p}")
    return raw


def parse_user_visible_history_from_artifact(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Return the public transcript list. Prefer top-level user_visible_history; fall back to
    trajectory.user_visible_history when bundles nest it under trajectory.
    """
    top = doc.get("user_visible_history")
    if isinstance(top, list) and top:
        return [_coerce_visible_row(item) for item in top]

    traj = doc.get("trajectory")
    if isinstance(traj, dict):
        nested = traj.get("user_visible_history")
        if isinstance(nested, list) and nested:
            return [_coerce_visible_row(item) for item in nested]

    raise ValueError("Dialogue JSON has no user_visible_history array (top-level or under trajectory)")


def _coerce_visible_row(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        return dict(item)
    return {"turn_idx": 0, "role": "unknown", "content": str(item), "timestamp": ""}


def format_user_visible_history_for_prompt(entries: list[dict[str, Any]]) -> str:
    """Turn visible-history rows into a single block for LLM system/user template substitution."""
    blocks: list[str] = []
    for row in entries:
        turn = row.get("turn_idx", "")
        role = row.get("role", "")
        raw_content = row.get("content")
        if isinstance(raw_content, str):
            content = raw_content.strip()
        else:
            content = json.dumps(raw_content, ensure_ascii=False) if raw_content is not None else ""
        ts = row.get("timestamp", "")
        head = f"[turn {turn}] {role}"
        if ts:
            head = f"{head} @ {ts}"
        blocks.append(f"{head}\n{content}")
    return "\n\n".join(blocks)


@dataclass(frozen=True)
class ExtractorInit:
    """Inputs for the POI extractor template: instruction, candidates, and public dialogue text."""

    user_instruction: str
    candidate_list: str
    user_visible_history_entries: tuple[dict[str, Any], ...]

    def prompt_format_kwargs(self) -> dict[str, str]:
        """Keys align with extractor placeholders in the prompt template."""
        return {
            "user_instruction": self.user_instruction,
            "candidate_list": self.candidate_list,
            "user_visible_history": format_user_visible_history_for_prompt(list(self.user_visible_history_entries)),
        }

    @classmethod
    def from_eval_record_and_dialogue_json(
        cls,
        record: EvalRecord,
        dialogue_json_path: Path | str,
        *,
        verify_task_id: bool = True,
    ) -> ExtractorInit:
        """
        Join one eval row with a saved run: instruction and candidates from the eval record,
        public transcript from the dialogue artifact.
        """
        path = Path(dialogue_json_path)
        doc = load_dialogue_artifact_json(path)
        if verify_task_id:
            task_block = doc.get("task")
            if isinstance(task_block, dict):
                tid = task_block.get("id")
                if tid is not None and str(tid).strip() != str(record.id):
                    raise ValueError(
                        f"Dialogue task id {tid!r} does not match eval record id {record.id} ({path})"
                    )
        entries = parse_user_visible_history_from_artifact(doc)
        return cls.from_record_and_visible_rows(record, entries)

    @classmethod
    def from_record_and_visible_rows(
        cls,
        record: EvalRecord,
        visible_rows: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    ) -> ExtractorInit:
        """Build extractor input from an eval row plus user-visible history rows (same shape as saved JSON)."""
        return cls(
            user_instruction=record.user_instruction.strip(),
            candidate_list=(record.candidate_list or "").strip(),
            user_visible_history_entries=tuple(visible_rows),
        )
