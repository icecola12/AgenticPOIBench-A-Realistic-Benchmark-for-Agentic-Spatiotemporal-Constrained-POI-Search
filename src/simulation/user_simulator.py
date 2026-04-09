"""
Simulated end-user turns via LiteLLM: system text comes from a YAML template plus per-sample
placeholders; completion output is stored as role "user". The API returns an assistant message
body, which we reinterpret as the user's line for the transcript.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from config import ResolvedConfig, load_yaml_dict
from concurrency import litellm_acompletion
from data import UserSimulatorInit


def load_user_simulator_prompt_template(prompt_yaml: Path) -> str:
    """Read the YAML mapping at path, return the string value under key 'user' (strip outer whitespace)."""
    data: dict[str, Any] = load_yaml_dict(prompt_yaml)
    raw = data.get("user")
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"prompt.yaml must define a non-empty string key 'user': {prompt_yaml}")
    return raw.strip()


def format_user_simulator_system_prompt(template: str, init: UserSimulatorInit) -> str:
    """Apply str.format with fields from init (user_instruction, location)."""
    return template.format(**init.prompt_format_kwargs())


def build_user_simulator_system_message(init: UserSimulatorInit, prompt_yaml: Path) -> dict[str, str]:
    """Build a single system chat message dict: role 'system', content from template + init."""
    template = load_user_simulator_prompt_template(prompt_yaml)
    content = format_user_simulator_system_prompt(template, init)
    return {"role": "system", "content": content}


def parse_user_simulator_output(content: str, stop_token: str) -> tuple[str, bool]:
    """
    Return (content, should_stop). should_stop is True if stop_token appears anywhere in content.
    """
    text = content if content is not None else ""
    terminated = stop_token in text
    return text, terminated


@dataclass
class UserSimulator:
    """Holds resolved settings, sample-specific init, and the prebuilt system message for one dialog."""

    resolved: ResolvedConfig
    init: UserSimulatorInit
    system_message: dict[str, str]

    @classmethod
    def from_init(cls, resolved: ResolvedConfig, init: UserSimulatorInit) -> UserSimulator:
        """Construct with system_message built from resolved.prompt_yaml and init."""
        system = build_user_simulator_system_message(init, resolved.prompt_yaml)
        return cls(resolved=resolved, init=init, system_message=system)

    @property
    def stop_token(self) -> str:
        return self.resolved.settings.dialog.stop_token

    @property
    def model(self) -> str:
        return self.resolved.settings.llm.user_model

    async def generate_user_message(
        self,
        dialogue_after_system: list[dict[str, str]],
    ) -> tuple[dict[str, str], bool]:
        """
        Call the chat model with [system_message] + dialogue_after_system; return the next user line
        and whether stop_token was found in the completion text.
        """
        messages: list[dict[str, str]] = [self.system_message, *dialogue_after_system]
        response = await litellm_acompletion(
            model=self.model,
            messages=messages,
            api_key=self.resolved.secrets.llm_api_key,
            api_base=self.resolved.llm_api_base_effective,
            temperature=self.resolved.settings.llm.temperature,
        )
        choice = response.choices[0]
        raw_content = choice.message.content
        raw = raw_content if isinstance(raw_content, str) else ("" if raw_content is None else str(raw_content))
        _, terminated = parse_user_simulator_output(raw, self.stop_token)
        # Transcript role is "user" even though the HTTP API speaks in assistant-shaped completions.
        user_msg: dict[str, str] = {"role": "user", "content": raw}
        return user_msg, terminated
