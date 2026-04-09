"""Concurrency caps aligned with config.yaml (mcp.max_concurrent_mcp, llm.max_concurrent_llm); see agent.md section 4.1."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Awaitable, Callable
from typing import Optional, TypeVar

from config import AppSettings, load_app_settings

T = TypeVar("T")

_mcp_async: Optional[asyncio.Semaphore] = None
_llm_async: Optional[asyncio.Semaphore] = None
_mcp_sync: Optional[threading.Semaphore] = None
_mcp_limit: int = 0
_llm_limit: int = 0


def init_concurrency(settings: AppSettings) -> None:
    """Initialize semaphores from parsed AppSettings (call explicitly to avoid ambiguous implicit load paths)."""
    global _mcp_async, _llm_async, _mcp_sync, _mcp_limit, _llm_limit
    _mcp_limit = settings.mcp.max_concurrent_mcp
    _llm_limit = settings.llm.max_concurrent_llm
    _mcp_async = asyncio.Semaphore(_mcp_limit)
    _llm_async = asyncio.Semaphore(_llm_limit)
    _mcp_sync = threading.Semaphore(_mcp_limit)


def _ensure_init() -> None:
    if _mcp_async is None:
        settings, _ = load_app_settings()
        init_concurrency(settings)


def get_mcp_semaphore() -> asyncio.Semaphore:
    """Async-side cap for Amap MCP / tool calls (matches yaml mcp.max_concurrent_mcp)."""
    _ensure_init()
    assert _mcp_async is not None
    return _mcp_async


def get_llm_semaphore() -> asyncio.Semaphore:
    """Async-side cap for LLM requests such as LiteLLM (matches yaml llm.max_concurrent_llm)."""
    _ensure_init()
    assert _llm_async is not None
    return _llm_async


def get_mcp_sync_semaphore() -> threading.Semaphore:
    """
    Same numeric cap as get_mcp_semaphore(), for in-process synchronous HTTP (e.g. requests)
    so sync paths do not bypass MCP limits before the stack is fully async.
    """
    _ensure_init()
    assert _mcp_sync is not None
    return _mcp_sync


def concurrency_limits() -> tuple[int, int]:
    """Return (mcp_limit, llm_limit) for the currently loaded configuration."""
    _ensure_init()
    return _mcp_limit, _llm_limit


async def run_sync_under_mcp_semaphore(fn: Callable[[], T]) -> T:
    """Run a synchronous callable in a thread pool under the MCP asyncio.Semaphore."""
    async with get_mcp_semaphore():
        return await asyncio.to_thread(fn)


async def litellm_acompletion(*args, **kwargs):
    """Call litellm.acompletion under the LLM asyncio.Semaphore."""
    import litellm

    async with get_llm_semaphore():
        return await litellm.acompletion(*args, **kwargs)


async def run_under_llm_semaphore(awaitable: Awaitable[T]) -> T:
    """Await any coroutine under the LLM semaphore (for async LLM calls other than acompletion)."""
    async with get_llm_semaphore():
        return await awaitable
