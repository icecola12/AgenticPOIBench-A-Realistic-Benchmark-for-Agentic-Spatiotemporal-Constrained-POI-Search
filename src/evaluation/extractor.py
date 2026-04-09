"""
LLM-based POI judge: reads public dialogue + instruction + candidate list, returns structured POI IDs.

Uses the same LiteLLM stack and concurrency cap as User Simulator / Agent.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal, Union

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from config import ResolvedConfig, load_yaml_dict
from concurrency import init_concurrency, litellm_acompletion
from data import ExtractorInit


class RecommendedPoi(BaseModel):
    """One POI line item in a successful judge output."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    name: str = ""
    id: str = Field(default="", validation_alias=AliasChoices("id", "poi_id"))


class ExtractorSuccessResult(BaseModel):
    """Parsed success branch: matched POIs with stable IDs from the candidate list."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    state: Literal["success"]
    pois: list[RecommendedPoi] = Field(default_factory=list)
    judgment_trace: str = Field(
        default="",
        validation_alias=AliasChoices("判断过程", "judgment_trace"),
        serialization_alias="判断过程",
    )


class ExtractorFailedResult(BaseModel):
    """Parsed failure branch: extraction or ID backtrace did not complete."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    state: Literal["failed"]
    reason: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    failed_pois: list[dict[str, Any]] = Field(default_factory=list)
    judgment_trace: str = Field(
        default="",
        validation_alias=AliasChoices("判断过程", "judgment_trace"),
        serialization_alias="判断过程",
    )


ExtractorJudgeResult = Union[ExtractorSuccessResult, ExtractorFailedResult]

_EXTRACTOR_YAML_KEYS: tuple[str, ...] = ("Extractor", "Exator")


def load_extractor_prompt_template(prompt_yaml: Path) -> str:
    """Load the extractor instruction block from the prompt YAML (supports legacy key spelling)."""
    data: dict[str, Any] = load_yaml_dict(prompt_yaml)
    for key in _EXTRACTOR_YAML_KEYS:
        raw = data.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    raise ValueError(
        f"prompt.yaml must define a non-empty extractor template under one of {_EXTRACTOR_YAML_KEYS!r}: {prompt_yaml}"
    )


def build_extractor_system_content(template: str, init: ExtractorInit) -> str:
    """
    Fill placeholders: user_instruction, candidate_list, user_visible_history.

    Uses literal replace instead of str.format so JSON examples in the template
    keep their braces.
    """
    kw = init.prompt_format_kwargs()
    out = template
    out = out.replace("{user_instruction}", kw["user_instruction"])
    out = out.replace("{candidate_list}", kw["candidate_list"])
    out = out.replace("{user_visible_history}", kw["user_visible_history"])
    return out


def _strip_markdown_json_fence(text: str) -> str:
    t = text.strip()
    m = re.match(r"^```(?:json)?\s*\n?", t, re.IGNORECASE)
    if m:
        t = t[m.end() :]
    if t.rstrip().endswith("```"):
        t = t.rstrip()[:-3].rstrip()
    return t.strip()


def _first_json_object_slice(text: str) -> str:
    """Take the outermost JSON object substring when the model adds chatter around it."""
    s = _strip_markdown_json_fence(text)
    start = s.find("{")
    if start < 0:
        return s
    depth = 0
    for i in range(start, len(s)):
        c = s[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1]
    return s[start:]


def parse_judge_json_text(raw: str) -> ExtractorJudgeResult:
    """
    Parse model output into a validated judge result.
    On JSON or schema failure, returns a synthetic failed result instead of raising.
    """
    try:
        blob = _first_json_object_slice(raw)
        obj: Any = json.loads(blob)
        if not isinstance(obj, dict):
            return ExtractorFailedResult(
                state="failed",
                reason="model_output_not_object",
                details={"raw_type": type(obj).__name__},
                judgment_trace="",
            )
        st = obj.get("state")
        if st == "success":
            return ExtractorSuccessResult.model_validate(obj)
        if st == "failed":
            return ExtractorFailedResult.model_validate(obj)
        return ExtractorFailedResult(
            state="failed",
            reason="missing_or_invalid_state",
            details={"state": st},
            judgment_trace=str(obj.get("判断过程", "")),
        )
    except (json.JSONDecodeError, ValueError) as e:
        return ExtractorFailedResult(
            state="failed",
            reason="json_parse_or_validate_error",
            details={"error": str(e)},
            judgment_trace="",
        )


def judge_agent_payload(result: ExtractorJudgeResult) -> dict[str, Any]:
    """Serialize judge output for embedding under evaluation.judge_agent (Chinese keys preserved)."""
    return result.model_dump(by_alias=True, mode="json")


def recommended_poi_ids(result: ExtractorJudgeResult) -> list[str]:
    """Flat ID list for evaluation.recommended_poi_ids; empty unless success with IDs."""
    if isinstance(result, ExtractorSuccessResult):
        out: list[str] = []
        for p in result.pois:
            pid = (p.id or "").strip()
            if pid:
                out.append(pid)
        return out
    return []


def evaluation_fields_from_judge(result: ExtractorJudgeResult) -> dict[str, Any]:
    """Bundle judge_agent + recommended_poi_ids for merging into an evaluation section."""
    return {
        "judge_agent": judge_agent_payload(result),
        "recommended_poi_ids": recommended_poi_ids(result),
    }


async def run_extractor(resolved: ResolvedConfig, init: ExtractorInit) -> ExtractorJudgeResult:
    """
    One LiteLLM call: system message is the filled extractor template; user nudge asks for raw JSON only.
    """
    init_concurrency(resolved.settings)
    template = load_extractor_prompt_template(resolved.prompt_yaml)
    system_text = build_extractor_system_content(template, init)
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_text},
        {
            "role": "user",
            "content": (
                "Reply with a single JSON object only, following the success or failure schema "
                "described in the system message. Do not wrap in markdown fences."
            ),
        },
    ]
    model = resolved.settings.llm.extract_model
    response = await litellm_acompletion(
        model=model,
        messages=messages,
        api_key=resolved.secrets.llm_api_key,
        api_base=resolved.llm_api_base_effective,
        temperature=resolved.settings.llm.temperature,
    )
    choice = response.choices[0]
    raw_content = choice.message.content
    raw = raw_content if isinstance(raw_content, str) else ("" if raw_content is None else str(raw_content))
    return parse_judge_json_text(raw)
