"""
Agent turn: LiteLLM chat with Amap map tools. Runs an inner loop of model calls and synchronous
tool execution (HTTP capped elsewhere) until the model returns text without tool calls or the
configured round limit is reached.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from config import ResolvedConfig, load_yaml_dict
from concurrency import litellm_acompletion, run_sync_under_mcp_semaphore
from data import AgentInit
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from tools.amap_tools import get_amap_tools


def load_agent_prompt_template(prompt_yaml: Path) -> str:
    """Load the Agent block from the prompt YAML file."""
    data: dict[str, Any] = load_yaml_dict(prompt_yaml)
    raw = data.get("Agent")
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"prompt.yaml must define a non-empty string key 'Agent': {prompt_yaml}")
    return raw.strip()


def format_agent_system_prompt(template: str, init: AgentInit) -> str:
    """Fill location, coordinate, and time placeholders for the agent system prompt."""
    return template.format(**init.prompt_format_kwargs())


def build_agent_system_message(init: AgentInit, prompt_yaml: Path) -> dict[str, str]:
    """Single system message dict for the agent."""
    template = load_agent_prompt_template(prompt_yaml)
    content = format_agent_system_prompt(template, init)
    return {"role": "system", "content": content}


def _tools_to_openai_definitions(tools: Sequence[BaseTool]) -> list[dict[str, Any]]:
    """OpenAI-compatible tool schemas for the chat completion API."""
    return [convert_to_openai_tool(t) for t in tools]


def _normalize_assistant_message(msg: Any) -> dict[str, Any]:
    """Turn a LiteLLM/OpenAI-style message object into a plain message dict for the next request."""
    if hasattr(msg, "model_dump") and callable(msg.model_dump):
        data = msg.model_dump()
    elif isinstance(msg, dict):
        data = dict(msg)
    else:
        data = {
            "role": "assistant",
            "content": getattr(msg, "content", None) or "",
        }
        tc = getattr(msg, "tool_calls", None)
        if tc:
            data["tool_calls"] = _serialize_tool_calls(tc)
        return data

    data.setdefault("role", "assistant")
    if data.get("content") is None:
        data["content"] = ""
    if data.get("tool_calls"):
        data["tool_calls"] = _serialize_tool_calls(data["tool_calls"])
    return data


def _serialize_tool_calls(tool_calls: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in tool_calls or []:
        if isinstance(item, dict):
            out.append(item)
            continue
        if hasattr(item, "model_dump") and callable(item.model_dump):
            out.append(item.model_dump())
            continue
        fn = getattr(item, "function", None)
        name = getattr(fn, "name", "") if fn is not None else ""
        args = getattr(fn, "arguments", "{}") if fn is not None else "{}"
        if not isinstance(args, str):
            args = json.dumps(args) if args is not None else "{}"
        out.append(
            {
                "id": getattr(item, "id", "") or "",
                "type": "function",
                "function": {"name": name, "arguments": args},
            }
        )
    return out


def _parse_tool_arguments(raw: str) -> dict[str, Any]:
    if not raw or not str(raw).strip():
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"_value": parsed}
    except json.JSONDecodeError:
        return {"_raw_arguments": raw}


@dataclass
class POIAgent:
    """Configured agent: system prompt, tool list, and one multi-step generation turn."""

    resolved: ResolvedConfig
    init: AgentInit
    system_message: dict[str, str]
    tools: list[BaseTool]

    @classmethod
    def from_init(cls, resolved: ResolvedConfig, init: AgentInit) -> POIAgent:
        system = build_agent_system_message(init, resolved.prompt_yaml)
        return cls(
            resolved=resolved,
            init=init,
            system_message=system,
            tools=list(get_amap_tools()),
        )

    @property
    def model(self) -> str:
        return self.resolved.settings.llm.agent_model

    @property
    def max_tool_rounds(self) -> int:
        return self.resolved.settings.llm.max_agent_tool_rounds

    def _tool_specs(self) -> list[dict[str, Any]]:
        return _tools_to_openai_definitions(self.tools)

    def _find_tool(self, name: str) -> BaseTool | None:
        for t in self.tools:
            if t.name == name:
                return t
        return None

    async def _run_tool(self, name: str, arguments_json: str) -> str:
        """Execute one tool under the MCP sync semaphore; return a string for the tool message."""
        tool = self._find_tool(name)
        if tool is None:
            return json.dumps({"error": "unknown_tool", "name": name}, ensure_ascii=False)
        args = _parse_tool_arguments(arguments_json)

        def _invoke() -> Any:
            return tool.invoke(args)

        try:
            result = await run_sync_under_mcp_semaphore(_invoke)
        except Exception as e:
            return json.dumps({"error": str(e), "tool": name}, ensure_ascii=False)
        if isinstance(result, str):
            return result
        try:
            return json.dumps(result, ensure_ascii=False, default=str)
        except TypeError:
            return str(result)

    async def generate_reply(self, dialogue_after_system: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        One agent turn: append assistant and tool messages until the model stops requesting tools.

        dialogue_after_system: messages after system (e.g. user / assistant / tool), same order as
        in the running transcript.

        Returns: new messages only (assistant/tool pairs and final assistant), to extend state.
        """
        prefix: list[dict[str, Any]] = [self.system_message, *dialogue_after_system]
        new_messages: list[dict[str, Any]] = []
        specs = self._tool_specs()

        for _ in range(self.max_tool_rounds):
            response = await litellm_acompletion(
                model=self.model,
                messages=prefix + new_messages,
                api_key=self.resolved.secrets.llm_api_key,
                api_base=self.resolved.llm_api_base_effective,
                temperature=self.resolved.settings.llm.temperature,
                tools=specs,
                tool_choice="auto",
            )
            choice = response.choices[0]
            raw_msg = choice.message
            assistant_msg = _normalize_assistant_message(raw_msg)
            new_messages.append(assistant_msg)

            tool_calls = assistant_msg.get("tool_calls") or []
            if not tool_calls:
                break

            for tc in tool_calls:
                fn = tc.get("function") or {}
                name = fn.get("name") or ""
                args = fn.get("arguments")
                if not isinstance(args, str):
                    args = json.dumps(args) if args is not None else "{}"
                tid = tc.get("id") or ""
                observation = await self._run_tool(name, args)
                new_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tid,
                        "content": observation,
                    }
                )

        return new_messages
