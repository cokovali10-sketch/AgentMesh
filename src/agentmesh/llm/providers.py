"""HTTP-клиент LLM (OpenAI-совместимый) и Anthropic-клиент.

Поддерживаются любые OpenAI-совместимые API (OpenAI, OpenRouter,
локальные vLLM/Ollama/llama.cpp) и Anthropic.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from agentmesh.core.message import Message, Role
from agentmesh.llm.base import LLMProviderError, parse_tool_arguments
# --- константы вынесены FORGE refactor ---
CONST_0_7 = 0.7
CONST_60 = 60.0
CONST_300 = 300
CONST_400 = 400



def _format_openai_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for t in tools:
        out.append(
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
                },
            }
        )
    return out


class OpenAICompatClient:
    """Клиент для любого OpenAI-совместимого API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        timeout: float = CONST_60,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not self.api_key and "api.openai.com" in base_url:
            raise LLMProviderError("OPENAI_API_KEY не задан (или передайте api_key)")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def chat(
        self,
        messages: list[Message],
        temperature: float = CONST_0_7,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> Message:
        payload: dict[str, Any] = {
            "model": self.model,
            "temperature": temperature,
            "messages": [m.to_llm_dict() for m in messages],
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if tools:
            payload["tools"] = _format_openai_tools(tools)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            if resp.status_code >= CONST_400:
                raise LLMProviderError(f"HTTP {resp.status_code}: {resp.text[:CONST_300]}")

        data = resp.json()
        choice = data["choices"][0]["message"]
        tool_calls = []
        for tc in choice.get("tool_calls") or []:
            tool_calls.append(
                {
                    "id": tc["id"],
                    "name": tc["function"]["name"],
                    "arguments": parse_tool_arguments(tc["function"]["arguments"]),
                }
            )
        return Message(
            role=Role.ASSISTANT,
            content=choice.get("content") or "",
            sender=self.model,
            tool_calls=tool_calls,
        )


class AnthropicClient:
    """Клиент Anthropic Claude."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-3-5-sonnet-latest",
        timeout: float = CONST_60,
    ) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            raise LLMProviderError("ANTHROPIC_API_KEY не задан (или передайте api_key)")
        self.model = model
        self.timeout = timeout

    async def chat(
        self,
        messages: list[Message],
        temperature: float = CONST_0_7,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> Message:
        system = "\n".join(m.content for m in messages if m.role == Role.SYSTEM)
        chat = [m.to_llm_dict() for m in messages if m.role != Role.SYSTEM]

        payload: dict[str, Any] = {
            "model": self.model,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "system": system or "Ты полезный ассистент.",
            "messages": chat,
        }
        if tools:
            payload["tools"] = tools  # Anthropic-совместимая схема

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
            if resp.status_code >= CONST_400:
                raise LLMProviderError(f"HTTP {resp.status_code}: {resp.text[:CONST_300]}")

        data = resp.json()
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        return Message(role=Role.ASSISTANT, content=text, sender=self.model)


__all__ = ["AnthropicClient", "LLMProviderError", "OpenAICompatClient"]
